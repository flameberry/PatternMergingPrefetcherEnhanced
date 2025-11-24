#include "pmp_adaptive_clip.h"
#include "custom_util.h"
#include "cache.h"
#include "ooo_cpu.h"

#include <bits/stdc++.h>
#include <random>

// =============================================================================
// CLIP Filter Implementation - COMPLETE
// =============================================================================

namespace clip {

// ============================================================================
// UtilityBuffer Implementation
// ============================================================================

UtilityBuffer::UtilityBuffer(int size) : size(size), head(0) {
    buffer.resize(size);
}

void UtilityBuffer::insert(uint64_t pf_address, uint64_t trigger_ip) {
    buffer[head].pf_address = pf_address;
    buffer[head].trigger_ip = trigger_ip;
    buffer[head].valid = true;
    head = (head + 1) % size;
}

std::pair<bool, uint64_t> UtilityBuffer::check_and_get_trigger_ip(uint64_t address) {
    for (int i = 0; i < size; i++) {
        if (buffer[i].valid && buffer[i].pf_address == address) {
            return {true, buffer[i].trigger_ip};
        }
    }
    return {false, 0};
}

void UtilityBuffer::clear() {
    for (auto& entry : buffer) {
        entry.valid = false;
    }
    head = 0;
}

// ============================================================================
// HistoryRegister Implementation
// ============================================================================

HistoryRegister::HistoryRegister(int length) : length(length), history(0) {}

void HistoryRegister::update(bool outcome) {
    history = ((history << 1) | (outcome ? 1 : 0)) & ((1ULL << length) - 1);
}

uint64_t HistoryRegister::get(){
    return history;
}

void HistoryRegister::reset() {
    history = 0;
}

// ============================================================================
// APCTracker Implementation
// ============================================================================

APCTracker::APCTracker() 
    : window_count(0), current_window_accesses(0), current_window_cycles(0) {
    window_apc_history.resize(APC_WINDOW_COUNT, 0.0);
}

void APCTracker::record_access() {
    current_window_accesses++;
}

void APCTracker::record_cycle() {
    current_window_cycles++;
}

bool APCTracker::check_phase_change(int window_size_accesses) {
    if (current_window_accesses < window_size_accesses) {
        return false;
    }
    
    double current_apc = 0.0;
    if (current_window_cycles > 0) {
        current_apc = (double)current_window_accesses / current_window_cycles;
    }
    
    window_apc_history[window_count % APC_WINDOW_COUNT] = current_apc;
    window_count++;
    
    current_window_accesses = 0;
    current_window_cycles = 0;
    
    if (window_count < APC_WINDOW_COUNT) {
        return false;
    }
    
    double avg_apc = get_average_apc();
    double change = std::abs(current_apc - avg_apc) / (avg_apc + 1e-9);
    
    return change > APC_CHANGE_THRESHOLD;
}

double APCTracker::get_average_apc(){
    double sum = 0.0;
    int count = std::min((int)window_count, APC_WINDOW_COUNT);
    
    for (int i = 0; i < count; i++) {
        sum += window_apc_history[i];
    }
    
    return sum / count;
}

void APCTracker::reset() {
    window_count = 0;
    current_window_accesses = 0;
    current_window_cycles = 0;
    std::fill(window_apc_history.begin(), window_apc_history.end(), 0.0);
}

// ============================================================================
// CriticalityFilter Implementation
// ============================================================================

void CriticalityFilter::record_rob_stall(uint64_t ip) {
    uint64_t key = build_key(ip);
    Entry* entry = Super::find(key);
    
    if (entry) {
        if (entry->data.crit_count < 65535) {
            entry->data.crit_count++;
        }
        Super::rp_promote(key);
    } else {
        CriticalityFilterData data;
        data.ip = ip;
        data.crit_count = 1;
        data.hit_count = 0;
        data.issue_count = 0;
        data.is_critical_and_accurate = false;
        
        Super::insert(key, data);
        Super::rp_insert(key);
    }
}

void CriticalityFilter::record_prefetch_issue(uint64_t ip) {
    uint64_t key = build_key(ip);
    Entry* entry = Super::find(key);
    
    if (entry) {
        if (entry->data.issue_count < 65535) {
            entry->data.issue_count++;
        }
        Super::rp_promote(key);
    }
}

void CriticalityFilter::record_prefetch_hit(uint64_t ip) {
    uint64_t key = build_key(ip);
    Entry* entry = Super::find(key);
    
    if (entry) {
        if (entry->data.hit_count < 65535) {
            entry->data.hit_count++;
        }
        Super::rp_promote(key);
    }
}

bool CriticalityFilter::is_critical_and_accurate(uint64_t ip) {
    uint64_t key = build_key(ip);
    Entry* entry = Super::find(key);
    
    if (!entry) {
        return false;
    }
    
    return entry->data.is_critical_and_accurate;
}

double CriticalityFilter::get_ip_accuracy(uint64_t ip) {
    uint64_t key = build_key(ip);
    Entry* entry = Super::find(key);
    
    if (!entry || entry->data.issue_count == 0) {
        return 0.0;
    }
    
    return (double)entry->data.hit_count / entry->data.issue_count;
}

void CriticalityFilter::update_after_exploration_window() {
    int marked_count = 0;  // For debug
    int critical_count = 0;  // For debug
    for (int set_idx = 0; set_idx < this->num_sets; set_idx++) {
        for (int way_idx = 0; way_idx < this->num_ways; way_idx++) {
            auto& entry = this->entries[set_idx][way_idx];
            if (!entry.valid) continue;

           bool is_critical = entry.data.crit_count >= CRITICALITY_COUNT_THRESHOLD;
            
            if (is_critical) {
                critical_count++;
            }

            bool is_accurate;
            if (entry.data.issue_count == 0) {
                // No prefetches issued yet (exploration window)
                // Give critical IPs a chance - assume they're accurate
                is_accurate = true;
            } else {
                // Have prefetch feedback - use actual accuracy
                double accuracy = (double)entry.data.hit_count / entry.data.issue_count;
                is_accurate = accuracy >= IP_ACCURACY_THRESHOLD;
            }

            if (is_critical && is_accurate) {
                entry.data.is_critical_and_accurate = true;
             }
            
            if (entry.data.is_critical_and_accurate) {
                marked_count++;
            }
        }
    }
    //   // IMPORTANT DEBUG OUTPUT
    // std::cout << "[CLIP] update_after_exploration_window(): " 
    //           << "Found " << critical_count << " critical IPs, "
    //           << "marked " << marked_count << " as critical_and_accurate" << std::endl;
}

void CriticalityFilter::reset_counts_with_hysteresis() {
     for (int set_idx = 0; set_idx < this->num_sets; set_idx++) {
        for (int way_idx = 0; way_idx < this->num_ways; way_idx++) {
            auto& entry = this->entries[set_idx][way_idx];
            if (!entry.valid) continue;
            
            entry.data.crit_count /= 2;
            entry.data.hit_count /= 2;
            entry.data.issue_count /= 2;
        }
    }
}

void CriticalityFilter::reset_all() {
     for (int set_idx = 0; set_idx < this->num_sets; set_idx++) {
        for (int way_idx = 0; way_idx < this->num_ways; way_idx++) {
            auto& entry = this->entries[set_idx][way_idx];
            entry.valid = false;
            entry.data = CriticalityFilterData();
        }
    }
}

std::string CriticalityFilter::log() {
    std::vector<std::string> headers({"IP", "Crit_Count", "Hit_Count", "Issue_Count", "Crit&Acc"});
    return Super::log(headers);
}

void CriticalityFilter::write_data(Entry& entry, custom_util::Table& table, int row) {
    table.set_cell(row, 0, entry.data.ip);
    table.set_cell(row, 1, entry.data.crit_count);
    table.set_cell(row, 2, entry.data.hit_count);
    table.set_cell(row, 3, entry.data.issue_count);
    table.set_cell(row, 4, entry.data.is_critical_and_accurate ? "YES" : "NO");
}

uint64_t CriticalityFilter::build_key(uint64_t ip) {
    return custom_util::hash_index(ip, this->index_len);
}

// ============================================================================
// CriticalityPredictor Implementation
// ============================================================================

bool CriticalityPredictor::predict_critical(uint64_t critical_signature) {
    uint64_t key = build_key(critical_signature);
    Entry* entry = Super::find(key);
    
    if (!entry) {
        return false;
    }
    
    Super::rp_promote(key);
    return entry->data.is_critical();
}

void CriticalityPredictor::train(uint64_t critical_signature, bool was_critical) {
    uint64_t key = build_key(critical_signature);
    Entry* entry = Super::find(key);
    
    if (entry) {
        if (was_critical) {
            entry->data.increment();
        } else {
            entry->data.decrement();
        }
        Super::rp_promote(key);
    } else {
        CriticalityPredictorData data;
        if (was_critical) {
            data.increment();
        } else {
            data.decrement();
        }
        
        Super::insert(key, data);
        Super::rp_insert(key);
    }
}

void CriticalityPredictor::reset_all() {
        for (int set_idx = 0; set_idx < this->num_sets; set_idx++) {
            for (int way_idx = 0; way_idx < this->num_ways; way_idx++) {
                auto& entry = this->entries[set_idx][way_idx];
                entry.valid = false;
                entry.data = CriticalityPredictorData();
        }
    }
}

std::string CriticalityPredictor::log() {
    std::vector<std::string> headers({"Signature", "Counter", "Prediction"});
    return Super::log(headers);
}

void CriticalityPredictor::write_data(Entry& entry, custom_util::Table& table, int row) {
    table.set_cell(row, 0, entry.key);
    table.set_cell(row, 1, (int)entry.data.saturating_counter);
    table.set_cell(row, 2, entry.data.is_critical() ? "CRITICAL" : "NOT_CRIT");
}

uint64_t CriticalityPredictor::build_key(uint64_t critical_signature) {
    return custom_util::hash_index(critical_signature, this->index_len);
}

// ============================================================================
// CLIPFilter Implementation
// ============================================================================

CLIPFilter::CLIPFilter(int cpu, int crit_filter_size, int crit_filter_ways,
                       int crit_pred_size, int crit_pred_ways,
                       int utility_buffer_size, int debug_level)
    : cpu(cpu)
    , crit_filter(crit_filter_size, crit_filter_ways, debug_level)
    , crit_predictor(crit_pred_size, crit_pred_ways, debug_level)
    , utility_buffer(utility_buffer_size)
    , branch_history(BRANCH_HISTORY_LENGTH)
    , criticality_history(CRITICALITY_HISTORY_LENGTH)
    , apc_tracker()
    , l1d_misses_in_window(0)
    , total_prefetch_candidates(0)
    , prefetches_issued(0)
    , prefetches_dropped_not_critical(0)
    , prefetches_dropped_low_accuracy(0)
    , critical_loads_detected(0)
    , phase_changes_detected(0)
    , debug_level(debug_level) {
    
    if (debug_level >= 1) {
        std::cout << "CLIPFilter::CLIPFilter(cpu=" << cpu 
                  << ", crit_filter_size=" << crit_filter_size
                  << ", crit_pred_size=" << crit_pred_size
                  << ", utility_buffer_size=" << utility_buffer_size
                  << ")" << std::endl;
    }
}

uint64_t CLIPFilter::compute_critical_signature(uint64_t ip, uint64_t address) {
    uint64_t signature = ip ^ address ^ branch_history.get() ^ criticality_history.get();
    return signature;
}

bool CLIPFilter::should_prefetch(uint64_t pf_address, uint64_t trigger_ip) {
    total_prefetch_candidates++;
    
    // Stage I: Check if trigger IP is critical and accurate
    if (!crit_filter.is_critical_and_accurate(trigger_ip)) {
        prefetches_dropped_not_critical++;
        
        if (debug_level >= 2) {
            std::cerr << "[CLIP] Dropped prefetch from IP " << std::hex << trigger_ip
                      << " (not critical or not accurate)" << std::dec << std::endl;
        }
        
        return false;
    }
    
    // // Stage II: Check dynamic criticality prediction
    // uint64_t crit_sig = compute_critical_signature(trigger_ip, pf_address);
    
    // if (!crit_predictor.predict_critical(crit_sig)) {
    //     prefetches_dropped_low_accuracy++;
        
    //     if (debug_level >= 2) {
    //         std::cerr << "[CLIP] Dropped prefetch: predictor says not critical" << std::dec << std::endl;
    //     }
        
    //     return false;
    // }
    
    prefetches_issued++;
    
    if (debug_level >= 2) {
        std::cout << "[CLIP] Allowing prefetch for IP " << std::hex << trigger_ip
                  << ", addr " << pf_address << std::dec << std::endl;
    }
    
    return true;
}

void CLIPFilter::record_rob_stall(uint64_t address, uint64_t ip, bool is_l1_miss) {
    // std::cout << "!!! ENTERING record_rob_stall, is_l1_miss=" << is_l1_miss << std::endl;
    if (!is_l1_miss) {
        std::cout << "!!! EARLY RETURN" << std::endl;
        return;
    }

    // std::cout << "!!! ABOUT TO INCREMENT, current=" << l1d_misses_in_window << std::endl;    
    critical_loads_detected++;
    crit_filter.record_rob_stall(ip);    
     l1d_misses_in_window++;  
     
      if (is_exploration_window_complete()) {  
          if (debug_level >= 1) {  
              std::cout << "[CLIP CPU" << cpu << "] Exploration window complete!" << std::endl;  // ← LINE 4
          }  
          end_exploration_window();  
      }  

    if (crit_filter.is_critical_and_accurate(ip)) {
        uint64_t crit_sig = compute_critical_signature(ip, address);
        crit_predictor.train(crit_sig, true);
    }
    
    criticality_history.update(true);
    
    if (debug_level >= 2) {
        std::cout << "[CLIP] ROB stall: IP=" << std::hex << ip 
                  << ", addr=" << address << std::dec << std::endl;
    }
}

void CLIPFilter::record_prefetch_issue(uint64_t pf_address, uint64_t trigger_ip) {
    utility_buffer.insert(pf_address, trigger_ip);
    crit_filter.record_prefetch_issue(trigger_ip);
    
    if (debug_level >= 2) {
        std::cout << "[CLIP] Prefetch issued: addr=" << std::hex << pf_address
                  << ", trigger_ip=" << trigger_ip << std::dec << std::endl;
    }
}

void CLIPFilter::record_demand_hit_on_prefetch(uint64_t address) {
    auto result = utility_buffer.check_and_get_trigger_ip(address);
    
    if (result.first) {
        uint64_t trigger_ip = result.second;
        crit_filter.record_prefetch_hit(trigger_ip);
        
        if (debug_level >= 2) {
            std::cout << "[CLIP] Demand hit on prefetch: addr=" << std::hex << address
                      << ", trigger_ip=" << trigger_ip << std::dec << std::endl;
        }
    }
    
    criticality_history.update(false);
}

void CLIPFilter::update_branch_history(bool taken) {
    branch_history.update(taken);
}

void CLIPFilter::cycle_operate() {
    apc_tracker.record_cycle();
    check_and_handle_phase_change();
}

bool CLIPFilter::is_exploration_window_complete(){
    // std::cout << "!!! CHECK: " << l1d_misses_in_window << " >= " << EXPLORATION_WINDOW_SIZE 
            //   << " = " << (l1d_misses_in_window >= EXPLORATION_WINDOW_SIZE) << std::endl;
    return l1d_misses_in_window >= EXPLORATION_WINDOW_SIZE;
}

void CLIPFilter::end_exploration_window() {
    if (debug_level >= 1) {
        std::cout << "[CLIP CPU" << cpu << "] Exploration window complete "
                  << "(misses=" << l1d_misses_in_window << ")" << std::endl;
    }
    
    crit_filter.update_after_exploration_window();
    // crit_filter.reset_counts_with_hysteresis();
    l1d_misses_in_window = 0;
    
    if (debug_level >= 1) {
        print_stats();
    }
}

void CLIPFilter::check_and_handle_phase_change() {
    if (apc_tracker.check_phase_change(EXPLORATION_WINDOW_SIZE)) {
        phase_changes_detected++;
        
        if (debug_level >= 1) {
            std::cout << "[CLIP CPU" << cpu << "] Phase change detected! Resetting." << std::endl;
        }
        
        crit_filter.reset_all();
        crit_predictor.reset_all();
        utility_buffer.clear();
        branch_history.reset();
        criticality_history.reset();
        l1d_misses_in_window = 0;
    }
}

void CLIPFilter::print_stats(){
    double drop_rate_crit = (total_prefetch_candidates > 0) ?
        100.0 * prefetches_dropped_not_critical / total_prefetch_candidates : 0.0;
    double drop_rate_acc = (total_prefetch_candidates > 0) ?
        100.0 * prefetches_dropped_low_accuracy / total_prefetch_candidates : 0.0;
    double issue_rate = (total_prefetch_candidates > 0) ?
        100.0 * prefetches_issued / total_prefetch_candidates : 0.0;
    
    std::cout << "[CLIP CPU" << cpu << " Stats]" << std::endl;
    std::cout << "  Total candidates:        " << total_prefetch_candidates << std::endl;
    std::cout << "  Prefetches issued:       " << prefetches_issued 
              << " (" << std::fixed << std::setprecision(1) << issue_rate << "%)" << std::endl;
    std::cout << "  Dropped (not critical):  " << prefetches_dropped_not_critical
              << " (" << drop_rate_crit << "%)" << std::endl;
    // std::cout << "  Dropped (low accuracy):  " << prefetches_dropped_low_accuracy
            //   << " (" << drop_rate_acc << "%)" << std::endl;
    std::cout << "  Critical loads detected: " << critical_loads_detected << std::endl;
    std::cout << "  Phase changes:           " << phase_changes_detected << std::endl;
}

std::string CLIPFilter::log(){
    std::stringstream ss;
    
    ss << "=== CLIP Filter ===" << std::endl;
    ss << "Criticality Filter:" << std::endl;
    ss << crit_filter.log() << std::endl;
    ss << "Criticality Predictor:" << std::endl;
    ss << crit_predictor.log() << std::endl;
    
    return ss.str();
}

} // namespace clip

// =============================================================================
// PMP Prefetcher Implementation - COMPLETE
// =============================================================================

namespace {
    const int DEBUG_LEVEL = 0;
    bool SUPPORT_VA = false;

    constexpr int PATTERN_LEN = (1 << pmp::IN_REGION_BITS) / BLOCK_SIZE;
    constexpr int FT_SIZE = 64;
    constexpr int FT_WAY = 8;
    constexpr int AT_SIZE = 32;
    constexpr int AT_WAY = 16;
    constexpr int OPT_WAYS = 1;
    constexpr int OPT_SIZE = (1 << pmp::OFFSET_BITS) * OPT_WAYS;
    constexpr int OFFSET_MAX_CONF = 32;
    constexpr int PPT_WAYS = 1;
    constexpr int PPT_SIZE = (1 << pmp::PC_BITS) * PPT_WAYS;
    constexpr int PC_MAX_CONF = 32;

    static std::vector<pmp::PMP> prefetchers;

} // namespace

namespace pmp {

// ============================================================================
// PrefetchBuffer::prefetch Implementation with CLIP Integration
// ============================================================================

int PrefetchBuffer::prefetch(PMP* pmp_parent, CACHE* cache, uint64_t block_address) {
    if (this->debug_level >= 2) {
        std::cerr << "PrefetchBuffer::prefetch(cache=" << cache->NAME << ", block_address=0x" << std::hex << block_address
                  << ")" << std::dec << std::endl;
        std::cerr << "[PrefetchBuffer::prefetch] " << cache->get_occupancy(3, 0) << "/" << cache->get_size(3, 0)
                  << " PQ entries occupied." << std::dec << std::endl;
        std::cerr << "[PrefetchBuffer::prefetch] " << cache->get_occupancy(0, 0) << "/" << cache->get_size(0, 0)
                  << " MSHR entries occupied." << std::dec << std::endl;
    }
    
    uint64_t base_addr = block_address << BOTTOM_BITS;
    int region_offset = __coarse_offset(__fine_offset(block_address));
    uint64_t region_number = block_address >> OFFSET_BITS;
    uint64_t key = this->build_key(region_number);
    Entry* entry = Super::find(key);
    
    if (!entry) {
        if (this->debug_level >= 2)
            std::cerr << "[PrefetchBuffer::prefetch] No entry found." << std::dec << std::endl;
        return 0;
    }
    
    Super::rp_promote(key);
    int pf_issued = 0;
    std::vector<int>& pattern = entry->data.pattern;
    pattern[region_offset] = 0;
    int pf_offset;
    DEBUG(cout << "[Prefetch Begin] base_addr " << std::hex << base_addr << ", " << std::dec;)

    // MSHR budget calculation
    uint32_t mshr_size = cache->get_size(0, 0);
    uint32_t prefetch_mshr_count = 0;
    
    for (uint32_t i = 0; i < cache->get_occupancy(0, 0); i++) {
        // Count prefetch MSHRs if possible
    }
    
    uint32_t reserved_for_demand = (uint32_t)(mshr_size * pmp_parent->demand_reserve_pct);
    uint32_t max_prefetch_budget = mshr_size - reserved_for_demand;
    
    if (this->debug_level >= 2) {
        std::cerr << "[PrefetchBuffer] MSHR Budget: "
                  << "Total=" << mshr_size 
                  << ", Reserved=" << reserved_for_demand
                  << ", PF_Budget=" << max_prefetch_budget << std::endl;
    }

    for (int d = 1; d < this->pattern_len; d += 1) {
        for (int sgn = +1; sgn >= -1; sgn -= 2) {
            pf_offset = region_offset + sgn * d;
            if (0 <= pf_offset && pf_offset < this->pattern_len && pattern[pf_offset] > 0) {
                DEBUG(cout << pf_offset << " ";)
                uint64_t pf_address = (region_number * this->pattern_len + pf_offset) << LOG2_BLOCK_SIZE;
                
                // MSHR safety checks
                uint32_t total_mshr_pressure = cache->get_occupancy(0, 0) + cache->get_occupancy(3, 0);
                uint32_t estimated_demand_mshrs = reserved_for_demand;
                bool within_budget = (total_mshr_pressure + 1) <= (mshr_size - estimated_demand_mshrs);
                bool pq_available = cache->get_occupancy(3, 0) < cache->get_size(3, 0);
                
                if (total_mshr_pressure < mshr_size && within_budget && pq_available) {
                    
                    // ========== CLIP FILTERING ==========
                    bool clip_allows = true;
                    if (pmp_parent->use_clip && pmp_parent->clip_filter) {
                        uint64_t trigger_ip = 0;
                        auto it = pmp_parent->region_to_trigger_ip.find(region_number);
                        if (it != pmp_parent->region_to_trigger_ip.end()) {
                            trigger_ip = it->second;
                        }
                        
                        clip_allows = pmp_parent->clip_filter->should_prefetch(pf_address, trigger_ip);
                        
                        if (!clip_allows && this->debug_level >= 2) {
                            std::cerr << "[PMP+CLIP] CLIP dropped prefetch: addr=" << std::hex 
                                      << pf_address << ", IP=" << trigger_ip << std::dec << std::endl;
                        }
                    }
                    // ========== END CLIP FILTERING ==========
                    
                    if (clip_allows) {
                        uint32_t pf_metadata = 0;
                        pf_metadata = __add_pf_sour_level(pf_metadata, 1);
                        if (pattern[pf_offset] == 1) {
                            pf_metadata = __add_pf_dest_level(pf_metadata, 1);
                        } else {
                            pf_metadata = __add_pf_dest_level(pf_metadata, 2);
                        }

                        int ok = cache->prefetch_line(pf_address, pattern[pf_offset] == 1 ? true : false, pf_metadata);
                        pf_issued += ok;
                        
                        if (ok && !cache->warmup) {
                            pmp_parent->record_prefetch_issue(pf_address);
                            
                            // Record CLIP prefetch issue
                            if (pmp_parent->use_clip && pmp_parent->clip_filter) {
                                uint64_t trigger_ip = 0;
                                auto it = pmp_parent->region_to_trigger_ip.find(region_number);
                                if (it != pmp_parent->region_to_trigger_ip.end()) {
                                    trigger_ip = it->second;
                                }
                                pmp_parent->clip_filter->record_prefetch_issue(pf_address, trigger_ip);
                            }
                            
                            if (pattern[pf_offset] == 1) {
                                prefetch_to_l1++;
                            } else {
                                prefetch_to_l2++;
                            }
                        }
                        pattern[pf_offset] = 0;
                    }
                    
                } else {
                    DEBUG(cout << std::endl;)
                    if (this->debug_level >= 2) {
                        std::cerr << "[PrefetchBuffer::prefetch] Throttled: "
                                  << "total_pressure=" << total_mshr_pressure << "/" << mshr_size
                                  << ", within_budget=" << within_budget 
                                  << ", pq_avail=" << pq_available << std::dec << std::endl;
                    }
                    return pf_issued;
                }
            }
        }
    }
    
    DEBUG(cout << std::endl;)
    Super::erase(key);
    return pf_issued;
}

// ============================================================================
// PMP::access Implementation with CLIP Integration
// ============================================================================

void PMP::access(uint64_t block_number, uint64_t pc) {
    // Check if the current access is a useful prefetch
    auto* inflight_entry = this->inflight_pf_tracker.find(this->inflight_pf_tracker.build_key(block_number));
    if (inflight_entry && !inflight_entry->data.used) {
        this->useful_prefetches++;
        inflight_entry->data.used = true;
        
        // CLIP: Record hit on prefetch
        if (use_clip && clip_filter) {
            uint64_t address = block_number << LOG2_BLOCK_SIZE;
            clip_filter->record_demand_hit_on_prefetch(address);
        }
    }

    if (this->debug_level >= 2)
        std::cerr << "[ PMP] access(block_number=0x" << std::hex << block_number << ", pc=0x" << pc << ")" << std::dec << std::endl;

    uint64_t region_number = block_number >> OFFSET_BITS;
    int region_offset = __fine_offset(block_number);
    
    // Track trigger IP for this region (CLIP needs this)
    region_to_trigger_ip[region_number] = pc;
    
    bool success = this->accumulation_table.set_pattern(region_number, __coarse_offset(region_offset));
    if (success)
        return;
        
    FilterTable::Entry* entry = this->filter_table.find(region_number);
    if (!entry) {
        this->filter_table.insert(region_number, region_offset, pc);
        std::vector<int> pattern = this->find_in_opt(pc, block_number);
        if (pattern.empty()) {
            return;
        }

        this->pf_buffer.insert(region_number, pattern);
        return;
    } else if (entry->data.offset != region_offset) {
        uint64_t region_number = custom_util::hash_index(entry->key, this->filter_table.get_index_len());
        AccumulationTable::Entry victim =
            this->accumulation_table.insert(region_number, entry->data.pc, entry->data.offset, region_offset);
        this->accumulation_table.set_pattern(region_number, __coarse_offset(region_offset));
        this->filter_table.erase(region_number);
        if (victim.valid) {
            invalid_by_max++;
            this->insert_in_opt(victim);
        }
    }
}

// ============================================================================
// PMP::eviction Implementation
// ============================================================================

void PMP::eviction(uint64_t block_number) {
    if (this->debug_level >= 2)
        std::cerr << "[ PMP] eviction(block_number=" << block_number << ")" << std::dec << std::endl;
    uint64_t region_number = block_number / this->pattern_len;
    this->filter_table.erase(region_number);
    AccumulationTable::Entry* entry = this->accumulation_table.erase(region_number);
    if (entry) {
        invalid_by_eviction++;
        this->insert_in_opt(*entry);
    }
}

// ============================================================================
// PMP::prefetch Implementation
// ============================================================================

int PMP::prefetch(CACHE* cache, uint64_t block_number) {
    if (this->debug_level >= 2)
        std::cerr << " PMP::prefetch(cache=" << cache->NAME << ", block_number=" << std::hex << block_number << ")" << std::dec
                  << std::endl;
    int pf_issued = this->pf_buffer.prefetch(this, cache, block_number);
    if (this->debug_level >= 2)
        std::cerr << "[ PMP::prefetch] pf_issued=" << pf_issued << std::dec << std::endl;
    return pf_issued;
}

// ============================================================================
// PMP Utility Methods
// ============================================================================

void PMP::set_debug_level(int debug_level) {
    this->filter_table.set_debug_level(debug_level);
    this->accumulation_table.set_debug_level(debug_level);
    this->opt.set_debug_level(debug_level);
    this->ppt.set_debug_level(debug_level);
    this->debug_level = debug_level;
}

void PMP::log() {
    std::cerr << "Filter table begin" << std::dec << std::endl;
    std::cerr << this->filter_table.log();
    std::cerr << "Filter table end" << std::endl;

    std::cerr << "Accumulation table begin" << std::dec << std::endl;
    std::cerr << this->accumulation_table.log();
    std::cerr << "Accumulation table end" << std::endl;

    std::cerr << "Offset pattern table begin" << std::dec << std::endl;
    std::cerr << this->opt.log();
    std::cerr << "Offset pattern table end" << std::endl;

    std::cerr << "PC pattern table begin" << std::dec << std::endl;
    std::cerr << this->ppt.log();
    std::cerr << "PC pattern table end" << std::endl;

    std::cerr << "Prefetch buffer begin" << std::dec << std::endl;
    std::cerr << this->pf_buffer.log();
    std::cerr << "Prefetch buffer end" << std::endl;
}

// ============================================================================
// PMP::find_in_opt Implementation
// ============================================================================

std::vector<int> PMP::find_in_opt(uint64_t pc, uint64_t block_number) {
    if (this->debug_level >= 2) {
        std::cerr << "[ PMP] find_in_opt(pc=0x" << std::hex << pc << ", address=0x" << block_number << ")" << std::dec << std::endl;
    }
    
    std::vector<OffsetPatternTableData> matches = this->opt.find(pc, block_number);
    std::vector<OffsetPatternTableData> matches_pc = this->ppt.find(pc, block_number);
    std::vector<int> pattern;
    std::vector<int> pattern_pc;
    std::vector<int> result_pattern(this->pattern_len, 0);
    
    if (!matches.empty()) {
        pattern = this->vote(matches);
        pattern_pc = this->vote(matches_pc, true);

#define ARBITRATION_APPROACH 1
#if ARBITRATION_APPROACH == 0
        if (pattern_pc.empty()) {
            for (int i = 0; i < this->pattern_len; i++) {
                result_pattern[i] = pattern[i];
            }
        } else {
            for (int i = 0; i < this->pattern_len; i++) {
                result_pattern[i] = pattern[i];
            }
        }
#elif ARBITRATION_APPROACH == 1
        if (pattern_pc.empty()) {
            for (int i = 0; i < this->pattern_len; i++) {
                result_pattern[i] = pattern[i] == FILL_L1_PMP ? FILL_L2_PMP : pattern[i] == FILL_L2_PMP ? FILL_LLC_PMP : 0;
            }
        } else {
            for (int i = 0; i < this->pattern_len; i++) {
                if (pattern[i] == FILL_L1_PMP && pattern_pc[i / PATTERN_DEGRADE_LEVEL] == FILL_L1_PMP) {
                    result_pattern[i] = FILL_L1_PMP;
                } else if (pattern[i] == FILL_L1_PMP || pattern_pc[i / PATTERN_DEGRADE_LEVEL] == FILL_L1_PMP || pattern[i] == FILL_L2_PMP || pattern_pc[i / PATTERN_DEGRADE_LEVEL] == FILL_L2_PMP) {
                    result_pattern[i] = FILL_L2_PMP;
                }
            }
        }
#elif ARBITRATION_APPROACH == 2
        if (pattern.empty()) {
            return result_pattern;
        }

        if (pattern_pc.empty()) {
            for (int i = 0; i < this->pattern_len; i++) {
                if (pattern[i] == FILL_L1_PMP) {
                    result_pattern[i] = FILL_L2_PMP;
                } else if (pattern[i] == FILL_L2_PMP) {
                    result_pattern[i] = FILL_LLC_PMP;
                } else {
                    result_pattern[i] = 0;
                }
            }
        } else {
            for (int i = 0; i < this->pattern_len; i++) {
                int opt_level = pattern[i];
                int ppt_level = pattern_pc[i / PATTERN_DEGRADE_LEVEL];

                if (opt_level == FILL_L1_PMP && ppt_level == FILL_L1_PMP) {
                    result_pattern[i] = FILL_L1_PMP;
                } else if (opt_level > 0 && ppt_level > 0) {
                    result_pattern[i] = FILL_L2_PMP;
                } else if (opt_level > 0 && ppt_level == 0) {
                    if (opt_level == FILL_L1_PMP) {
                        result_pattern[i] = FILL_L2_PMP;
                    } else if (opt_level == FILL_L2_PMP) {
                        result_pattern[i] = FILL_LLC_PMP;
                    }
                } else {
                    result_pattern[i] = 0;
                }
            }
        }
#endif
    }

    int offset = __coarse_offset(__fine_offset(block_number));
    result_pattern = custom_util::my_rotate(result_pattern, +offset);
    return result_pattern;
}

// ============================================================================
// PMP::insert_in_opt Implementation
// ============================================================================

void PMP::insert_in_opt(const AccumulationTable::Entry& entry) {
    uint64_t region_number = custom_util::hash_index(entry.key, this->accumulation_table.get_index_len());
    uint64_t address = (region_number << OFFSET_BITS) + entry.data.offset;
    if (this->debug_level >= 2) {
        std::cerr << "[ PMP] insert_in_opt(" << std::hex << " address=0x" << address << ")" << std::dec << std::endl;
    }
    const std::vector<bool>& pattern = entry.data.pattern;
    std::vector<bool> pattern_copy = pattern;
      if (!pattern_copy.empty()) {
        pattern_copy[0] = true;  // Mark trigger offset
    }
    if (custom_util::count_bits(custom_util::pattern_to_int(pattern)) != 1) {
        this->opt.insert(address, entry.data.pc, pattern_copy, false, entry.data.second_offset);
        this->ppt.insert(address, entry.data.pc, custom_util::pattern_degrade(pattern_copy, PATTERN_DEGRADE_LEVEL), true, entry.data.second_offset);
    }
}

// ============================================================================
// PMP::vote Implementation
// ============================================================================

std::vector<int> PMP::vote(const std::vector<OffsetPatternTableData>& x, bool is_pc_opt) {
    if (this->debug_level >= 2)
        std::cerr << " PMP::vote(...)" << std::endl;
    int n = x.size();
    if (n == 0) {
        if (this->debug_level >= 2)
            std::cerr << "[ PMP::vote] There are no voters." << std::endl;
        return std::vector<int>();
    }

    if (this->debug_level >= 2) {
        std::cerr << "[ PMP::vote] Taking a vote among:" << std::endl;
        for (int i = 0; i < n; i += 1)
            std::cerr << "<" << std::setw(3) << i + 1 << "> " << custom_util::pattern_to_string(x[i].pattern) << std::endl;
    }
    
    bool pf_flag = false;
    int pattern_len = is_pc_opt ? this->pattern_len / PATTERN_DEGRADE_LEVEL : this->pattern_len;
    std::vector<int> res(pattern_len, 0);

    for (int i = 0; i < pattern_len; i += 1) {
        int cnt = 0;
        for (int j = 0; j < n; j += 1) {
            cnt += x[j].pattern[i];
        }
        double p = 1.0 * cnt / x[0].pattern[0];
        if (p > 1) {
            std::cout << "cnt:" << cnt << ",total:" << x[0].pattern[0] << std::endl;
            assert(p <= 1);
        }

        if (x[0].pattern[0] <= START_CONF) {
            break;
        }

        if (is_pc_opt) {
            if (p >= PC_L1D_THRESH)
                res[i] = FILL_L1_PMP;
            else if (p >= PC_L2C_THRESH)
                res[i] = FILL_L2_PMP;
            else if (p >= PC_LLC_THRESH)
                res[i] = FILL_LLC_PMP;
            else
                res[i] = 0;
        } else {
            if (p >= L1D_THRESH)
                res[i] = FILL_L1_PMP;
            else if (p >= L2C_THRESH)
                res[i] = FILL_L2_PMP;
            else if (p >= LLC_THRESH)
                res[i] = FILL_LLC_PMP;
            else
                res[i] = 0;
        }
    }
    
    if (this->debug_level >= 2) {
        std::cerr << "<res> " << custom_util::pattern_to_string(res) << std::endl;
    }

    return res;
}

// ============================================================================
// PMP Adaptive Mechanism Implementation
// ============================================================================

void PMP::record_prefetch_issue(uint64_t pf_addr) {
    uint64_t pf_block = pf_addr >> LOG2_BLOCK_SIZE;
    auto evicted = this->inflight_pf_tracker.insert(this->inflight_pf_tracker.build_key(pf_block), {});
    if (evicted.valid && !evicted.data.used) {
        uint64_t age = this->cycle_count - evicted.data.issue_cycle;
        if (age < PREFETCH_TIMEOUT_CYCLES) {
            this->useless_prefetches++;
        }
    }
}

void PMP::record_prefetch_eviction(uint64_t pf_addr) {
    uint64_t pf_block = pf_addr >> LOG2_BLOCK_SIZE;
    auto* entry = this->inflight_pf_tracker.find(this->inflight_pf_tracker.build_key(pf_block));
    
    if (entry && !entry->data.used) {
        this->useless_prefetches++;
        this->inflight_pf_tracker.erase(this->inflight_pf_tracker.build_key(pf_block));
    }
}

// ============================================================================
// PMP::cycle_operate Implementation with Adaptive Logic
// ============================================================================

void PMP::cycle_operate() {
    	// Define constants for the adaptive mechanism


    cycle_count++;
    
    // CLIP cycle operation
    if (use_clip && clip_filter) {
        clip_filter->cycle_operate();
    }
    
    if (cycle_count < ADAPTIVE_INTERVAL) {
        return;
    }

    // Adapt MSHR reservation based on demand blocking
    if (demand_miss_total_count > 50) {
        double block_rate = (double)demand_miss_blocked_count / demand_miss_total_count;
        
        if (block_rate > 0.05) {
            this->demand_reserve_pct = std::min(0.50, this->demand_reserve_pct + 0.05);
            if (this->debug_level >= 1) {
                std::cerr << "[PMP Adaptive] Demand blocking high (" << block_rate 
                          << "), increasing reserve to " << this->demand_reserve_pct << std::endl;
            }
        } else if (block_rate < 0.01) {
            this->demand_reserve_pct = std::max(0.10, this->demand_reserve_pct - 0.05);
            if (this->debug_level >= 1) {
                std::cerr << "[PMP Adaptive] Demand blocking low (" << block_rate 
                          << "), decreasing reserve to " << this->demand_reserve_pct << std::endl;
            }
        }
        
        demand_miss_blocked_count = 0;
        demand_miss_total_count = 0;
    }


    // Interval reached, perform adaptation
	uint64_t total_evaluated = useful_prefetches + useless_prefetches;
	if (total_evaluated > 50) { // Only adapt if we have a meaningful number of samples
		double current_accuracy = (double)useful_prefetches / total_evaluated;

		if (current_accuracy > HIGH_ACCURACY_TARGET) {
			// Too conservative, get more aggressive
			this->L1D_THRESH = std::max(MIN_L1D_THRESH, this->L1D_THRESH - THRESHOLD_STEP);
			//this->reserved_mshrs = 1; // High accuracy -> Be aggressive
		} else if (current_accuracy < LOW_ACCURACY_TARGET) {
			// Too aggressive, get more conservative
			this->L1D_THRESH = std::min(MAX_L1D_THRESH, this->L1D_THRESH + THRESHOLD_STEP);
			//this->reserved_mshrs = 4; // Low accuracy -> Be conservative
		} else {
			//this->reserved_mshrs = 2; // Moderate accuracy -> Default
		}

		// Update L2C threshold to be proportional
		this->L2C_THRESH = this->L1D_THRESH * this->L2C_THRESH_RATIO;
	}

	// Reset for the next interval
	this->useful_prefetches = 0;
	this->useless_prefetches = 0;
	this->cycle_count = 0;
}
    
// ============================================================================
// PMP::record_load_completion for CLIP ROB stall tracking
// ============================================================================

void PMP::record_load_completion(uint64_t address, uint64_t ip, bool is_l1_miss, 
                                  int latency, bool rob_was_stalled) {
    if (!use_clip || !clip_filter) {
        return;
    }
    
    if (is_l1_miss && rob_was_stalled) {
        clip_filter->record_rob_stall(address, ip, true);
        
        if (debug_level >= 2) {
            std::cout << "[PMP+CLIP] Critical load detected: IP=" << std::hex 
                      << ip << ", addr=" << address << std::dec << std::endl;
        }
    }
}

// ============================================================================
// PMP Constructor Implementation
// ============================================================================

PMP::PMP(int pattern_len, int offset_width, int opt_size, int opt_max_conf, int opt_ways, 
         int pc_width, int ppt_size, int ppt_max_conf, int ppt_ways, 
         int filter_table_size, int ft_way, int accumulation_table_size, int at_way, 
         int pf_buffer_size, int pf_buffer_way,
         int FILL_L1, int FILL_L2, int FILL_LLC,
         int debug_level, int cpu)
    : pattern_len(pattern_len)
    , opt(opt_size, pattern_len, offset_width, opt_ways, opt_max_conf, debug_level, cpu)
    , ppt(ppt_size, pattern_len / PATTERN_DEGRADE_LEVEL, pc_width, ppt_ways, ppt_max_conf, debug_level, cpu)
    , filter_table(filter_table_size, debug_level, ft_way)
    , accumulation_table(accumulation_table_size, pattern_len, debug_level, at_way)
    , pf_buffer(pf_buffer_size, pattern_len, debug_level, pf_buffer_way)
    , L1D_THRESH(0.50)
    , L2C_THRESH(0.150)
    , inflight_pf_tracker(pf_buffer_size * 8, pf_buffer_way * 4)
    , FILL_L1_PMP(1)
    , FILL_L2_PMP(2)
    , FILL_LLC_PMP(3)
    , debug_level(debug_level)
    , cpu(cpu)
    , clip_filter(nullptr)
    , use_clip(true) {
    
    if (this->debug_level >= 1) {
        std::cerr << " PMP:: PMP(pattern_len=" << pattern_len
                  << ", filter_table_size=" << filter_table_size
                  << ", accumulation_table_size=" << accumulation_table_size
                  << ", pf_buffer_size=" << pf_buffer_size
                  << ", inflight_tracker_size=" << (pf_buffer_size * 8)
                  << ", debug_level=" << debug_level << ")" << std::endl;
    }
    
    // Initialize CLIP filter
    if (use_clip) {
        clip_filter = std::make_unique<clip::CLIPFilter>(
            cpu, 128, 4, 512, 4, 64, debug_level);
        
        if (this->debug_level >= 1) {
            std::cout << "[PMP+CLIP] CLIP filter enabled for CPU " << cpu << std::endl;
        }
    }
}

} // namespace pmp

// =============================================================================
// CACHE Interface Functions
// =============================================================================

void CACHE::prefetcher_initialize() {
    std::cout << NAME << " PMP Adaptive prefetcher CLIP Filter" << std::endl;
    
    prefetchers.reserve(NUM_CPUS);
    for (int cpu = 0; cpu < NUM_CPUS; cpu++) {
        prefetchers.emplace_back(
            PATTERN_LEN, pmp::OFFSET_BITS, OPT_SIZE, OFFSET_MAX_CONF, OPT_WAYS,
            pmp::PC_BITS, PPT_SIZE, PC_MAX_CONF, PPT_WAYS, FT_SIZE, FT_WAY,
            AT_SIZE, AT_WAY, pmp::PF_BUFFER_SIZE, pmp::PF_BUFFER_WAY,
            FILL_L1, FILL_L2, FILL_LLC, DEBUG_LEVEL, cpu
        );
    }
}

uint32_t CACHE::prefetcher_cache_operate(uint64_t addr, uint64_t ip, uint8_t cache_hit, 
                                          uint8_t type, uint32_t metadata_in) {

    
    if (DEBUG_LEVEL >= 2) {
        std::cerr << "CACHE::l1d_prefetcher_operate(addr=0x" << std::hex << addr << ", ip=0x" << ip << ", cache_hit=" << std::dec
                  << (int)cache_hit << ", type=" << (int)type << ")" << std::dec << std::endl;
        std::cerr << "[CACHE::l1d_prefetcher_operate] CACHE{core=" << this->cpu << ", NAME=" << this->NAME << "}" << std::dec
                  << std::endl;
    }

    if (type != LOAD)
        return metadata_in;

    uint64_t block_number = addr >> pmp::BOTTOM_BITS;

    if (!cache_hit && this->NAME.find("L1D") != std::string::npos && !this->warmup) {
        //std::cout << "[CACHE] Calling record_load_completion" << std::endl;
        prefetchers[cpu].record_load_completion(addr, ip, true, 200, true);
    }

    prefetchers[cpu].access(block_number, ip);
    prefetchers[cpu].prefetch(this, block_number);

    if (DEBUG_LEVEL >= 3) {
        prefetchers[cpu].log();
        std::cerr << "=======================================" << std::dec << std::endl;
    }
    return metadata_in;
}

uint32_t CACHE::prefetcher_cache_fill(uint64_t addr, uint32_t set, uint32_t way, 
                                       uint8_t prefetch, uint64_t evicted_addr, 
                                       uint32_t metadata_in) {
    uint64_t evicted_block_number = evicted_addr >> LOG2_BLOCK_SIZE;

    if (this->block[set * NUM_WAY + way].valid == 0)
        return metadata_in;

    for (int i = 0; i < NUM_CPUS; i += 1) {
        if (!block[set * NUM_WAY + way].prefetch)
            prefetchers[i].eviction(evicted_block_number);
    }
    return metadata_in;
}

void CACHE::prefetcher_cycle_operate() {
    prefetchers[cpu].cycle_operate();
}

void CACHE::prefetcher_final_stats() {
    std::cout << "Prefetch Request to L1: " << pmp::prefetch_to_l1 << ", "
              << "Prefetch Request to L2: " << pmp::prefetch_to_l2 << std::endl;
    std::cout << "Invalid by Eviction: " << prefetchers[cpu].invalid_by_eviction << std::endl;
    std::cout << "Invalid by Max: " << prefetchers[cpu].invalid_by_max << std::endl;
    std::cout << "Final L1D Threshold: " << std::fixed << std::setprecision(3) 
              << prefetchers[cpu].L1D_THRESH << std::endl;
    std::cout << "Final Demand Reserve: " << std::fixed << std::setprecision(1)
              << (prefetchers[cpu].demand_reserve_pct * 100) << "%" << std::endl;
    
    // CLIP statistics
    if (prefetchers[cpu].use_clip && prefetchers[cpu].clip_filter) {
        std::cout << "\n╔═══════════════════════════════════════╗" << std::endl;
        std::cout << "║       CLIP Filter Statistics         ║" << std::endl;
        std::cout << "╚═══════════════════════════════════════╝" << std::endl;
        prefetchers[cpu].clip_filter->print_stats();
        std::cout << std::endl;
    }
    
    prefetchers[cpu].log();
    std::cout << "Filter by PPT: " << pmp::filter_by_ppt << std::endl;
}