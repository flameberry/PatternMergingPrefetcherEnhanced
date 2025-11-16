// pmp_enhanced.cc - Complete standalone implementation with CLIP

#include "pmp_enhanced.h"
#include "custom_util.h"

#include <bits/stdc++.h>
#include <random>

#include "cache.h"
#include "champsim.h"

#include <iomanip>  // for std::setw, std::setprecision
#include <tuple>    // for std::tuple

namespace pmp_enhanced {

// Global counters
double pmp_recent_acc = 0.0;
int filter_by_ppt = 0;
int prefetch_to_l1 = 0, prefetch_to_l2 = 0;

// Static storage
static std::vector<PMP> prefetchers;
static std::unordered_map<uint64_t, uint64_t> region_trigger_map;
static std::unordered_map<uint64_t, int> consecutive_misses;

// ============================================================================
// CLIP Implementation
// ============================================================================

namespace clip {

CLIPFilter::CLIPFilter(int cpu_id)
    : cpu_id_(cpu_id),
      criticality_history_(0),
      exploration_miss_count_(0),
      exploration_windows_completed_(0),
      in_exploration_phase_(true), 
      total_prefetches_(0),
      dropped_prefetches_(0),
      enabled_(true) {
}

void CLIPFilter::process_access(uint64_t addr, uint64_t ip, bool rob_stalled,  bool is_miss) {
    if (!enabled_) return;
    
    // ========================================================================
    // Update criticality filter on ROB stalls
    // ========================================================================
    if (rob_stalled && is_miss) {
        update_on_stall(ip);
    }
    
    // ========================================================================
    // Check utility buffer for prefetch accuracy
    // ========================================================================
    check_utility(addr);

    // ========================================================================
    // UPDATE CRITICALITY PREDICTOR (ADD THIS SECTION)
    // Train the predictor based on whether this access was critical
    // ========================================================================
    uint64_t sig = build_signature(ip, addr);
    
    if (crit_predictor_.find(sig) != crit_predictor_.end() || 
        crit_predictor_.size() < MAX_PREDICTOR_ENTRIES) {
        
        uint8_t& counter = crit_predictor_[sig];
        
        if (rob_stalled && is_miss) {
            // Critical access - increment (saturating at 7)
            if (counter < 7) counter++;
        } else {
            // Non-critical access - decrement (saturating at 0)
            if (counter > 0) counter--;
        }
    }
    

    // ========================================================================
    // Exploration window management
    // ========================================================================
    if (is_miss) {
        exploration_miss_count_++;
        if (exploration_miss_count_ >= EXPLORATION_WINDOW*50) {
            reset_exploration_window();
        }
    }
}

bool CLIPFilter::should_issue_prefetch(uint64_t pf_addr, uint64_t trigger_ip) {
    if (!enabled_) return true;
    
    total_prefetches_++;
    uint64_t ip_tag = get_ip_tag(trigger_ip);

    if (in_exploration_phase_) {
        // Track IP during exploration
        if (crit_filter_.find(ip_tag) == crit_filter_.end() && 
            crit_filter_.size() < MAX_FILTER_ENTRIES) {
            crit_filter_[ip_tag] = CriticalityEntry();
        }
        return true;  // Allow everything during exploration
    }

    // DEBUG STATEMENTS
    // static uint64_t debug_counter = 0;
    // if (++debug_counter % 1000000 == 0) {
    //     std::cout << "[CLIP DEBUG] Candidates: " << total_prefetches_ 
    //               << ", Dropped: " << dropped_prefetches_ 
    //               << ", IPs tracked: " << crit_filter_.size() << std::endl;
    // }

    // Post-exploration filtering
    auto cf_it = crit_filter_.find(ip_tag);
    
    // ========================================================================
    // STAGE 1: Handle unknown IPs
    // ========================================================================
    if (cf_it == crit_filter_.end()) {
        // IP not in criticality filter yet
        
        if (crit_filter_.size() < MAX_FILTER_ENTRIES) {
            crit_filter_[ip_tag] = CriticalityEntry();
            return true;
        }
        dropped_prefetches_++;
        return false;
        }
    
    // ========================================================================
    // STAGE 2: Check if we have enough history for this IP
    // ========================================================================
    
    // int min_samples = (cf_it->second.crit_count >= 4) ? 32 : 16;
    int min_samples = 16;
    // const int MIN_ISSUES_FOR_DECISION = 8;
    if (cf_it->second.issue_count < min_samples) {
        // Still gathering data for this IP
        return true;  // Allow prefetch to continue learning
    }

    double accuracy = cf_it->second.get_accuracy();
    bool is_critical = (cf_it->second.crit_count >= 2);
    static uint64_t dropped_by_low_accuracy_critical = 0;
    static uint64_t dropped_by_low_accuracy_noncritical = 0;
    static uint64_t dropped_by_no_criticality = 0;
    static uint64_t dropped_by_predictor = 0;
    // ========================================================================
    // STAGE 3: Check if IP is critical
    // ========================================================================
    if (cf_it->second.crit_count == 0 /*&& accuracy < 0.30*/) {
            dropped_by_no_criticality++;
            dropped_prefetches_++;
            return false;
    }

    // ========================================================================
    // STAGE 4: If we have history, check accuracy
    // ========================================================================
    if (is_critical) {
       
        if (accuracy < 0.15) { // Reduced from 0.50
            dropped_by_low_accuracy_critical++;
            dropped_prefetches_++;
            return false;
        }
    }
    else{
          if (accuracy < 0.25) {
            dropped_by_low_accuracy_noncritical++;
            dropped_prefetches_++;
            return false;
        }
    }
        // if (!cf_it->second.is_critical_and_accurate()) {
        //     dropped_prefetches_++;
        //     return false;
        // }
    // }
    
    // ========================================================================
    // STAGE 5: Dynamic criticality prediction using signature
    // ========================================================================
    uint64_t sig = build_signature(trigger_ip, pf_addr);
    auto cp_it = crit_predictor_.find(sig);
    
    if (cp_it == crit_predictor_.end()) {
        // First time seeing this signature
        if (crit_predictor_.size() < MAX_PREDICTOR_ENTRIES) {
            // Initialize at threshold (middle value for 3-bit counter)
            crit_predictor_[sig] = 4;
        }
        return true;  // Allow new signatures
    }

    if (pmp_recent_acc > 0.60) {
        cp_it->second = std::min(7, static_cast<int>(cp_it->second + 1));  // +1 boost (saturate 7)
        //if (debug_level >= 2) std::cerr << "[CLIP] PMP high acc boost: counter=" << (int)cp_it->second << " (PMP acc=" << pmp_recent_acc << ")" << std::endl;
    }else if (pmp_recent_acc < 0.40) {
        cp_it->second = std::max(0, static_cast<int>(cp_it->second - 1));
    }
    
    // Check saturating counter's MSB
    // For 3-bit counter: 0-3 (MSB=0), 4-7 (MSB=1)
    if (cp_it->second < 4) {
        dropped_by_predictor++;
        dropped_prefetches_++;
        return false;
    }

    // if (total_prefetches_ % 1000000 == 0) {
    // std::cout << "[CLIP CPU" << cpu_id_ << "] Breakdown:" << std::endl;
    // std::cout << "  No criticality: " << dropped_by_no_criticality << std::endl;
    // std::cout << "  Low accuracy (critical): " << dropped_by_low_accuracy_critical << std::endl;
    // std::cout << "  Low accuracy (non-crit): " << dropped_by_low_accuracy_noncritical << std::endl;
    // std::cout << "  Predictor: " << dropped_by_predictor << std::endl;
// }
    
    return true;
}

void CLIPFilter::record_prefetch_issue(uint64_t pf_addr, uint64_t trigger_ip) {
    if (!enabled_) return;
    // static int count = 0;
    // if (++count % 10000 == 0) {
    //     std::cout << "[CLIP] Recorded " << count << " prefetch issues" << std::endl;
    // }

    uint64_t ip_tag = get_ip_tag(trigger_ip);

    // Convert to cache line address (64-byte aligned)
    uint64_t pf_line = pf_addr >> LOG2_BLOCK_SIZE;

     // Evict oldest if full
        if (utility_order_.size() >= UTILITY_BUF_SIZE) {
            uint64_t oldest = utility_order_.front();
            utility_order_.pop_front();
            utility_map_.erase(oldest);
        }
        
        // Add new entry
        utility_map_[pf_line] = {ip_tag, true};
        utility_order_.push_back(pf_line);
        
    
    // if (utility_buffer_.size() >= UTILITY_BUF_SIZE) {
    //     utility_buffer_.pop_front();
    // }
    // utility_buffer_.push_back({ip_tag, pf_line, true});
    
    auto& entry = crit_filter_[ip_tag];
    if (entry.issue_count < 63) {
        entry.issue_count++;
    }
}

void CLIPFilter::print_stats() const {
    if (!enabled_) {
        std::cout << "CLIP: Disabled" << std::endl;
        return;
    }
    
    std::cout << "\n=== CLIP Statistics (CPU " << cpu_id_ << ") ===" << std::endl;
    std::cout << "Enabled: Yes" << std::endl;
    std::cout << "Exploration windows completed: " << exploration_windows_completed_ << std::endl;
    std::cout << "Currently in exploration: " << (in_exploration_phase_ ? "Yes" : "No") << std::endl;
    std::cout << "Total prefetch candidates: " << total_prefetches_ << std::endl;
    std::cout << "Dropped by CLIP: " << dropped_prefetches_;
    
    if (total_prefetches_ > 0) {
        double drop_pct = 100.0 * dropped_prefetches_ / total_prefetches_;
        std::cout << " (" << std::fixed << std::setprecision(2) << drop_pct << "%)";
    }
    std::cout << std::endl;
    
    int critical_accurate = 0;
    int static_critical = 0;
    int dynamic_critical = 0;
    
    for (const auto& [ip, entry] : crit_filter_) {
        if (entry.is_critical_and_accurate()) {
            critical_accurate++;
            if (entry.get_accuracy() > 0.95) {
                static_critical++;
            } else {
                dynamic_critical++;
            }
        }
    }
    
    std::cout << "Critical IPs tracked: " << crit_filter_.size() << std::endl;
    std::cout << "Critical and accurate IPs: " << critical_accurate << std::endl;
    std::cout << "  Static-critical: " << static_critical << std::endl;
    std::cout << "  Dynamic-critical: " << dynamic_critical << std::endl;
    std::cout << "Predictor entries: " << crit_predictor_.size() << std::endl;
    
    print_top_ips(10);
}

uint64_t CLIPFilter::build_signature(uint64_t ip, uint64_t addr) const {
    uint64_t sig = ip;
    sig ^= (addr >> 6);
    sig ^= (static_cast<uint64_t>(criticality_history_) << 32);
    sig = sig ^ (sig >> 9) ^ (sig >> 18);
    return sig & 0x1FF;
}

void CLIPFilter::update_on_stall(uint64_t ip) {
    uint64_t ip_tag = get_ip_tag(ip);
    
    if (crit_filter_.size() >= MAX_FILTER_ENTRIES && 
        crit_filter_.find(ip_tag) == crit_filter_.end()) {
        return;
    }
    
    auto& entry = crit_filter_[ip_tag];
    if (entry.crit_count < 63) {
        entry.crit_count++;
    }
    
    criticality_history_ = (criticality_history_ << 1) | 1;
    
    uint64_t sig = build_signature(ip, 0);
    if (crit_predictor_.size() < MAX_PREDICTOR_ENTRIES) {
        uint8_t& sat = crit_predictor_[sig];
        if (sat < 7) sat++;
    }
}

void CLIPFilter::check_utility(uint64_t demand_addr) {
    // Convert to cache line address
    uint64_t demand_line = demand_addr >> LOG2_BLOCK_SIZE;

    // for (auto& ub : utility_buffer_) {
    //     if (ub.valid && ub.pf_line == demand_line) {
    //         auto& entry = crit_filter_[ub.ip_tag];
    //         if (entry.hit_count < 63) {
    //             entry.hit_count++;
    //         }

    //         static int hit_count = 0;
    //         if (++hit_count % 100 == 0) {
    //             std::cout << "[CLIP] Utility hits: " << hit_count << std::endl;
    //         }

    //         ub.valid = false;
    //         break;
    //     }
    // }
      auto it = utility_map_.find(demand_line);
        if (it != utility_map_.end() && it->second.second) {
            uint64_t ip_tag = it->second.first;
            
            auto& entry = crit_filter_[ip_tag];
            if (entry.hit_count < 63) {
                entry.hit_count++;
            }
            
            // Mark as used
            it->second.second = false;
            
            static int hit_count = 0;
            // if (++hit_count % 100 == 0) {
            //     std::cout << "[CLIP] Utility hits: " << hit_count << std::endl;
            // }
        }
}

void CLIPFilter::reset_exploration_window() {
    exploration_windows_completed_++;
    
    // After exploration window, we have training data
    // Can now start being selective about prefetches
    if (exploration_windows_completed_ >= 2) {
        in_exploration_phase_ = false;
    }

     // Age the counters (paper: "reset to half")
    for (auto& [ip, entry] : crit_filter_) {
        entry.hit_count >>= 1;
        entry.issue_count >>= 1;
        entry.crit_count >>= 1; // Newly added
    }
    
     // Remove entries with no activity (hysteresis cleanup)
    for (auto it = crit_filter_.begin(); it != crit_filter_.end(); ) {
        if (it->second.hit_count == 0 && 
            it->second.issue_count == 0 && 
            it->second.crit_count == 0) {
            it = crit_filter_.erase(it);
        } else {
            ++it;
        }
    }
    
    exploration_miss_count_ = 0;
}

void CLIPFilter::print_top_ips(int count) const {
    std::vector<std::pair<uint64_t, CriticalityEntry>> sorted_ips;
    for (const auto& p : crit_filter_) {
        sorted_ips.push_back(p);
    }
    
    std::sort(sorted_ips.begin(), sorted_ips.end(),
              [](const auto& a, const auto& b) {
                  return a.second.crit_count > b.second.crit_count;
              });
    
    int num_to_show = std::min(count, static_cast<int>(sorted_ips.size()));
    if (num_to_show > 0) {
        std::cout << "\nTop " << num_to_show << " Critical IPs:" << std::endl;
        for (int i = 0; i < num_to_show; i++) {
            const auto& [ip, entry] = sorted_ips[i];
            std::cout << "  IP 0x" << std::hex << ip << std::dec
                      << ": crit=" << static_cast<int>(entry.crit_count)
                      << ", acc=" << std::fixed << std::setprecision(3)
                      << entry.get_accuracy()
                      << " (" << static_cast<int>(entry.hit_count)
                      << "/" << static_cast<int>(entry.issue_count) << ")"
                      << (entry.is_critical_and_accurate() ? " [ACTIVE]" : "")
                      << std::endl;
        }
    }
}

} // namespace clip

// ============================================================================
// PMP Implementation
// ============================================================================

void PMP::access(uint64_t block_number, uint64_t pc) {
    if (this->debug_level >= 2)
        std::cerr << "[ PMP] access(block_number=0x" << std::hex << block_number << ", pc=0x" << pc << ")" << std::dec << std::endl;

    uint64_t region_number = block_number >> OFFSET_BITS;
    int region_offset = fine_offset(block_number);
    bool success = this->accumulation_table.set_pattern(region_number, coarse_offset(region_offset));
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
        this->accumulation_table.set_pattern(region_number, coarse_offset(region_offset));
        this->filter_table.erase(region_number);
        if (victim.valid) {
            invalid_by_max++;
            this->insert_in_opt(victim);
        }
    }
}

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

// int PMP::prefetch(CACHE* cache, uint64_t block_number, uint64_t trigger_ip,
//                  bool rob_stalled, uint8_t miss_level) {

//     static uint64_t prefetch_calls = 0;
//     static uint64_t should_issue_calls = 0;
//     prefetch_calls++;

    
//     if (this->debug_level >= 2)
//         std::cerr << " PMP::prefetch(cache=" << cache->NAME << ", block_number=" << std::hex << block_number << ")" << std::dec
//                   << std::endl;

//     // CLIP training
//     uint64_t addr = block_number << LOG2_BLOCK_SIZE;
//     clip_filter.process_access(addr, trigger_ip, rob_stalled, miss_level);

//     uint64_t region_number = block_number >> OFFSET_BITS;
//     uint64_t base_addr = block_number << BOTTOM_BITS;
//     int region_offset = __coarse_offset(__fine_offset(block_number));
    
//     // Get pattern from buffer
//     auto* entry = pf_buffer.get_entry_for_region(region_number);
//     if (!entry || !entry->valid) return 0;
    
//     int pf_issued = 0;
//     std::vector<int>& pattern = entry->data.pattern;
    
//     // Safety check: ensure pattern is not empty and offset is valid
//     if (pattern.empty() || region_offset < 0 || region_offset >= static_cast<int>(pattern.size())) {
//         return 0;
//     }
    
//     pattern[region_offset] = 0;
    
//     // Issue prefetches with CLIP filtering
//     for (int d = 1; d < this->pattern_len; d++) {
//         for (int sgn : {+1, -1}) {
//             int pf_offset = region_offset + sgn * d;
            
//             if (pf_offset < 0 || pf_offset >= static_cast<int>(pattern.size())) continue;
//             if (pattern[pf_offset] <= 0) continue;
            
//             uint64_t pf_address = (region_number * this->pattern_len + pf_offset) << LOG2_BLOCK_SIZE;
            
//             // CLIP filtering
//             should_issue_calls++;  // Count how many times we check
//             if (clip_filter.is_enabled() && 
//                 !clip_filter.should_issue_prefetch(pf_address, trigger_ip)) {
//                 pattern[pf_offset] = 0;
//                 continue;
//             }
            
//             // Check resources
//             if (cache->get_occupancy(3, 0) + cache->get_occupancy(0, 0) >= cache->get_size(0, 0) - 1) {
//                 break;
//             }
//             if (cache->get_occupancy(3, 0) >= cache->get_size(3, 0)) {
//                 break;
//             }
            
//             // Issue prefetch
//             uint32_t pf_metadata = 0;
//             pf_metadata = __add_pf_sour_level(pf_metadata, 1);
//             if (pattern[pf_offset] == 1) {
//                 pf_metadata = __add_pf_dest_level(pf_metadata, 1);
//             } else {
//                 pf_metadata = __add_pf_dest_level(pf_metadata, 2);
//             }
            
//             int ok = cache->prefetch_line(0, base_addr, pf_address, pattern[pf_offset] == 1, pf_metadata);
//             pf_issued += ok;
            
//             if (ok && !cache->warmup) {
//                 if (pattern[pf_offset] == 1) {
//                     prefetch_to_l1++;
//                 } else {
//                     prefetch_to_l2++;
//                 }
                
//                 // Record for CLIP
//                 if (clip_filter.is_enabled()) {
//                     clip_filter.record_prefetch_issue(pf_address, trigger_ip);

//                     // DEBUG STATEMENTS
//                     static int record_count = 0;
//                     if (++record_count % 10000 == 0) {
//                         std::cout << "[DEBUG] Recorded " << record_count 
//                                 << " prefetch issues" << std::endl;
//                     }
//                 }
//             }
//             pattern[pf_offset] = 0;
//         }
//     }

//     if (prefetch_calls % 10000 == 0) {
//         std::cout << "Ratio: " << (double)should_issue_calls / prefetch_calls << std::endl;
//     }
    
//     return pf_issued;
// }

// int PMP::prefetch(CACHE* cache, uint64_t block_number, uint64_t trigger_ip,
//                  bool rob_stalled, uint8_t miss_level) {
    
//     if (this->debug_level >= 2)
//         std::cerr << " PMP::prefetch(cache=" << cache->NAME << ", block_number=" << std::hex << block_number << ")" << std::dec
//                   << std::endl;

//     // CLIP training
//     uint64_t addr = block_number << LOG2_BLOCK_SIZE;
//     // clip_filter.process_access(addr, trigger_ip, rob_stalled, miss_level);

//     uint64_t region_number = block_number >> OFFSET_BITS;
//     uint64_t base_addr = block_number << BOTTOM_BITS;
//     int region_offset = __coarse_offset(__fine_offset(block_number));
    
//     // Get pattern from buffer
//     auto* entry = pf_buffer.get_entry_for_region(region_number);
//     if (!entry || !entry->valid) return 0;
    
//     int pf_issued = 0;
//     std::vector<int>& pattern = entry->data.pattern;
    
//     // Safety check: ensure pattern is not empty and offset is valid
//     if (pattern.empty() || region_offset < 0 || region_offset >= static_cast<int>(pattern.size())) {
//         return 0;
//     }
    
//     pattern[region_offset] = 0;
    
//     // Collect valid prefetch candidates FIRST
//     std::vector<std::pair<int, uint64_t>> candidates;
//     for (int d = 1; d < this->pattern_len; d++) {
//         for (int sgn : {+1, -1}) {
//             int pf_offset = region_offset + sgn * d;
            
//             if (pf_offset < 0 || pf_offset >= static_cast<int>(pattern.size())) continue;
//             if (pattern[pf_offset] <= 0) continue;
            
//             uint64_t pf_address = (region_number * this->pattern_len + pf_offset) << LOG2_BLOCK_SIZE;
//             candidates.push_back({pf_offset, pf_address});
//         }
//     }

//     // Now process candidates with CLIP filtering
//     for (auto& [pf_offset, pf_address] : candidates) {
//             // CLIP filtering
//              if (clip_filter.is_enabled() && 
//                 !clip_filter.should_issue_prefetch(pf_address, trigger_ip)) {
//                 pattern[pf_offset] = 0;
//                 continue;  // CLIP rejected this prefetch
//             }

//             // bool clip_allowed = true;
//             // if (clip_filter.is_enabled()){
//             //     clip_allowed = clip_filter.should_issue_prefetch(pf_address, trigger_ip);
            
//             //      // Record ALL candidates that pass CLIP filtering
//             //     // (This records the "intent to prefetch" regardless of resource availability)
//             //     if (clip_allowed) {
//             //         clip_filter.record_prefetch_issue(pf_address, trigger_ip);
//             //     }
//             // }

//             // if (!clip_allowed) {
//             //     pattern[pf_offset] = 0;
//             //     continue;
//             // }
            
//             // Check resources
//             if (cache->get_occupancy(3, 0) + cache->get_occupancy(0, 0) >= cache->get_size(0, 0) - 1) {
//                 break;
//             }
//             if (cache->get_occupancy(3, 0) >= cache->get_size(3, 0)) {
//                 break;
//             }
            
//             // Issue prefetch
//             uint32_t pf_metadata = 0;
//             pf_metadata = __add_pf_sour_level(pf_metadata, 1);
//             if (pattern[pf_offset] == 1) {
//                 pf_metadata = __add_pf_dest_level(pf_metadata, 1);
//             } else {
//                 pf_metadata = __add_pf_dest_level(pf_metadata, 2);
//             }
            
//             int ok = cache->prefetch_line(0, base_addr, pf_address, pattern[pf_offset] == 1, pf_metadata);
            
//             if(ok) {
//                 pf_issued++;
//             }
            
//             if (ok && !cache->warmup && clip_filter.is_enabled()) {
//                 clip_filter.record_prefetch_issue(pf_address, trigger_ip);
//                 if (pattern[pf_offset] == 1) {
//                     prefetch_to_l1++;
//                 } else {
//                     prefetch_to_l2++;
//                 }
//             }
//             pattern[pf_offset] = 0;
//         }
    
//     return pf_issued;
// }


// int PMP::prefetch(CACHE* cache, uint64_t block_number, uint64_t trigger_ip, 
//                   bool rob_stalled, uint8_t miss_level) {
//     if (debug_level >= 2)
//         std::cerr << "[PMP] prefetch(cache=" << cache->NAME << ", block=0x" << std::hex << block_number << ")" << std::dec << std::endl;

//     // // Fix 5: Trigger check (paper: only on FT offset match)
//     // uint64_t region_number = block_number >> OFFSET_BITS;
//     // int region_offset = __fine_offset(block_number);
//     // FilterTable::Entry* ft_entry = filter_table.find(region_number);
//     // if (!ft_entry || region_offset != ft_entry->data.offset) {
//     //     if (debug_level >= 2) std::cerr << "[PMP] Not trigger - skip" << std::endl;
//     //     return 0;
//     // }

//      // Get region info
//     uint64_t region_number = block_number >> OFFSET_BITS;
//     int region_offset = __fine_offset(block_number);
    
//     // Check if we have a pattern for this region
//     auto* entry = pf_buffer.get_entry_for_region(region_number);
//     if (!entry || !entry->valid) {
//         if (debug_level >= 2) std::cerr << "[PMP] No PB entry" << std::endl;
//         return 0;
//     }
//     // Fix 1: CLIP training (uncomment + on stall)
//     // uint64_t addr = block_number << LOG2_BLOCK_SIZE;
//     // clip_filter.process_access(addr, trigger_ip, rob_stalled, miss_level);  // Train on stall

//     // Fix 3: Correct base_addr (region byte base)
//     // uint64_t base_addr = region_number << (OFFSET_BITS + BOTTOM_BITS);  // 11-bit region * 64B lines to bytes

//     // Get PB entry (paper IV.B: extract from buffered)
//     auto* entry = pf_buffer.get_entry_for_region(region_number);
//     if (!entry || !entry->valid) {
//         if (debug_level >= 2) std::cerr << "[PMP] No PB entry" << std::endl;
//         return 0;
//     }
    
//     std::vector<int>& pattern = entry->data.pattern;
//     if (pattern.empty() || region_offset < 0 || region_offset >= static_cast<int>(pattern.size())) {
//         return 0;
//     }
    
//     pattern[region_offset] = 0;  // Mark trigger accessed

//      uint64_t base_addr = region_number << (OFFSET_BITS + LOG2_BLOCK_SIZE);

//     // Fix 4: Forward candidates with circular rotation (paper: shift left from trigger)
//     std::vector<std::pair<int, uint64_t>> candidates;
//     for (int d = 1; d < pattern_len; d++) {
//         int pf_offset = (region_offset + d) % pattern_len;  // Forward circular
//         if (pattern[pf_offset] <= 0) continue;

//         uint64_t pf_address = base_addr + (pf_offset << LOG2_BLOCK_SIZE);
//         candidates.push_back({pf_offset, pf_address});
//     }

//     // Fix 10: Degree limit (paper 4/access; Change 3: MSHR-aware)
//     int mshr_occ = cache->get_occupancy(3, 0);
//     int mshr_size = cache->get_size(3, 0);
//     int adaptive_degree = std::min(4, mshr_size - mshr_occ);  // Max 4, reserve MSHR

//     int pf_issued = 0;
//     for (auto& [pf_offset, pf_address] : candidates) {
//         if (pf_issued >= adaptive_degree) break;  // Throttle

//         // Fix 7: Adaptive thresh (Change 2: skip if freq < thresh)
//         int trigger_total = pattern[0];  // Dynamic total (trigger count from PB entry)
//         double freq = trigger_total > 0 ? static_cast<double>(pattern[pf_offset]) / trigger_total : 0.0;
//         if (freq < adaptive_l1d_thresh) {
//             pattern[pf_offset] = 0;
//             continue;
//         }

//         // Fix 6: MSHR reserve only
//         if (mshr_occ >= mshr_size - 1) break;

//         // Fix 1: CLIP filter
//         if (clip_filter.is_enabled() && !clip_filter.should_issue_prefetch(pf_address, trigger_ip)) {
//             pattern[pf_offset] = 0;
//             continue;
//         }

//         // Issue (paper: to L1 if freq>=0.50, L2 >=0.15; ChampSim prefetch_line)
//         uint32_t pf_metadata = 0;
//         pf_metadata = __add_pf_sour_level(pf_metadata, 1);  // Source L1D
//         int dest_level = (freq >= adaptive_l1d_thresh) ? 1 : 2;  // Adaptive L1/L2
//         pf_metadata = __add_pf_dest_level(pf_metadata, dest_level);
        
//         int ok = cache->prefetch_line(0, base_addr, pf_address, dest_level == 1, pf_metadata);
        
//         if (ok) {
//             pf_issued++;
//             // Fix 8: Record ALL issued (not just L1/!warmup)
//             clip_filter.record_prefetch_issue(pf_address, trigger_ip);
//             if (dest_level == 1) prefetch_to_l1++;
//             else prefetch_to_l2++;
//         }
        
//         pattern[pf_offset] = 0;  // Mark issued
//         mshr_occ++;  // Approx update (real from cache)
//     }
    
//     // Fix 11: PB invalid if max issued
//     if (pf_issued >= adaptive_degree) {
//         invalid_by_max++;
//         entry->valid = false;  // Invalidate PB
//     }

//     // // Change 4: Faster reset (call if high misses)
//     // if (rob_stalled && miss_level > 0) {
//     //     clip_filter.process_access(base_addr, trigger_ip, true, miss_level);  // Ensure training
//     // }

//     if (debug_level >= 1) std::cerr << "[PMP] Issued " << pf_issued << " from " << candidates.size() << " candidates (degree=" << adaptive_degree << ")" << std::endl;
//     return pf_issued;
// }

int PMP::prefetch(CACHE* cache, uint64_t block_number, uint64_t trigger_ip, 
                  bool rob_stalled, uint8_t miss_level) {
    if (debug_level >= 2)
        std::cerr << "[PMP] prefetch(cache=" << cache->NAME << ", block=0x" 
                  << std::hex << block_number << ")" << std::dec << std::endl;

    // Get region info
    uint64_t region_number = block_number >> OFFSET_BITS;
    int region_offset = fine_offset(block_number);
    
    // Check if we have a pattern for this region
    auto* entry = pf_buffer.get_entry_for_region(region_number);
    if (!entry || !entry->valid) {
        if (debug_level >= 2) std::cerr << "[PMP] No PB entry" << std::endl;
        return 0;
    }
    
    std::vector<int>& pattern = entry->data.pattern;
    if (pattern.empty() || region_offset < 0 || 
        region_offset >= static_cast<int>(pattern.size())) {
        return 0;
    }
    
    // Correct base_addr (region byte base)
    uint64_t base_addr = region_number << (OFFSET_BITS + LOG2_BLOCK_SIZE);
    
    pattern[region_offset] = 0;  // Mark trigger accessed

    // Collect prefetch candidates
    std::vector<std::pair<int, uint64_t>> candidates;
    for (int d = 1; d < pattern_len; d++) {
        for (int sgn : {+1, -1}) {  // Check both directions
            int pf_offset = region_offset + sgn * d;
            
            if (pf_offset < 0 || pf_offset >= static_cast<int>(pattern.size())) 
                continue;
            if (pattern[pf_offset] <= 0) 
                continue;

            uint64_t pf_address = base_addr + (pf_offset << LOG2_BLOCK_SIZE);
            candidates.push_back({pf_offset, pf_address});
        }
    }

    // Adaptive degree with MSHR awareness
    int mshr_occ = cache->get_occupancy(3, 0);
    int mshr_size = cache->get_size(3, 0);
    int adaptive_degree;

     if (mshr_occ > mshr_size * 0.85) {
        // CRITICAL: Near saturation - minimal prefetching
        adaptive_degree = 1;
    } else if (mshr_occ > mshr_size * 0.70) {
        // HIGH PRESSURE: Conservative prefetching
        adaptive_degree = std::min(2, mshr_size - mshr_occ);
    } else{
        // MODERATE PRESSURE: Reduced prefetching
        adaptive_degree = std::min(4, mshr_size - mshr_occ);
    }

    if (mshr_occ >= mshr_size - 1) {
        if (debug_level >= 1)
            std::cerr << "[PMP] MSHR full, blocking all prefetches" << std::endl;
        return 0;
    }

    int pf_issued = 0;
    for (auto& [pf_offset, pf_address] : candidates) {
        if (pf_issued >= adaptive_degree) break;
        
        // MSHR check
        if (mshr_occ >= mshr_size - 1) break;

        // CLIP filtering
        if (clip_filter.is_enabled() && 
            !clip_filter.should_issue_prefetch(pf_address, trigger_ip)) {
            pattern[pf_offset] = 0;
            continue;
        }

        // Determine destination level based on pattern confidence
        uint32_t pf_metadata = 0;
        pf_metadata = __add_pf_sour_level(pf_metadata, 1);
        int dest_level = (pattern[pf_offset] == 1) ? 1 : 2;
        pf_metadata = __add_pf_dest_level(pf_metadata, dest_level);
        
        int ok = cache->prefetch_line(0, base_addr, pf_address, 
                                      dest_level == 1, pf_metadata);
        
        if (ok) {
            pf_issued++;
             if (clip_filter.is_enabled()) {
                clip_filter.record_prefetch_issue(pf_address, trigger_ip);
            }
            if (!cache->warmup) {
                // clip_filter.record_prefetch_issue(pf_address, trigger_ip);
                if (dest_level == 1) prefetch_to_l1++;
                else prefetch_to_l2++;
            }
        }
        
        pattern[pf_offset] = 0;
        mshr_occ++;
    }

    if (debug_level >= 1) 
        std::cerr << "[PMP] Issued " << pf_issued << " from " 
                  << candidates.size() << " candidates" << std::endl;
    
    return pf_issued;
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
}

std::vector<int> PMP::find_in_opt(uint64_t pc, uint64_t block_number) {
   if (this->debug_level >= 2) {
        std::cerr << "[ PMP] find_in_opt(pc=0x" << std::hex << pc 
                  << ", address=0x" << block_number << ")" << std::dec << std::endl;
    }
    
    std::vector<OffsetPatternTableData> matches = this->opt.find(pc, block_number);
    std::vector<OffsetPatternTableData> matches_pc = this->ppt.find(pc, block_number);
    std::vector<int> result_pattern(this->pattern_len, 0);
    
    if (!matches.empty()) {
        std::vector<int> pattern = this->vote(matches, false);
        
        if (!matches_pc.empty()) {
            std::vector<int> pattern_pc = this->vote(matches_pc, true);
            
            // Combine OPT and PPT patterns with full cache hierarchy support
            for (int i = 0; i < this->pattern_len; i++) {
                int pc_idx = i / PATTERN_DEGRADE_LEVEL;
                int opt_level = pattern[i];
                int ppt_level = pattern_pc[pc_idx];
                
                // Both agree on L1 → highest confidence, prefetch to L1
                if (opt_level == FILL_L1_PMP && ppt_level == FILL_L1_PMP) {
                    result_pattern[i] = FILL_L1_PMP;
                }
                // At least one wants L1 or L2 → medium confidence, prefetch to L2
                else if (opt_level == FILL_L1_PMP || ppt_level == FILL_L1_PMP ||
                         opt_level == FILL_L2_PMP || ppt_level == FILL_L2_PMP) {
                    result_pattern[i] = FILL_L2_PMP;
                }
                // At least one wants LLC → low confidence, prefetch to LLC
                else if (opt_level == FILL_LLC_PMP || ppt_level == FILL_LLC_PMP) {
                    result_pattern[i] = FILL_LLC_PMP;
                }
                // Both weak or disagree → don't prefetch
                else {
                    result_pattern[i] = 0;
                }
            }
        } else {
            // No PC pattern available, use OPT pattern directly (includes LLC)
            result_pattern = pattern;
        }
    }
    
    int offset = coarse_offset(fine_offset(block_number));
    result_pattern = custom_util::my_rotate(result_pattern, +offset);
    return result_pattern;
}

void PMP::insert_in_opt(const AccumulationTable::Entry& entry) {
    uint64_t region_number = custom_util::hash_index(entry.key, this->accumulation_table.get_index_len());
    uint64_t address = (region_number << OFFSET_BITS) + entry.data.offset;
    if (this->debug_level >= 2) {
        std::cerr << "[ PMP] insert_in_opt(" << std::hex << " address=0x" << address << ")" << std::dec << std::endl;
    }
    const std::vector<bool>& pattern = entry.data.pattern;
    if (custom_util::count_bits(custom_util::pattern_to_int(pattern)) != 1) {
        this->opt.insert(address, entry.data.pc, pattern, false, entry.data.second_offset);
        this->ppt.insert(address, entry.data.pc, custom_util::pattern_degrade(pattern, PATTERN_DEGRADE_LEVEL), true, entry.data.second_offset);
    }
}

std::vector<int> PMP::vote(const std::vector<OffsetPatternTableData>& x, bool is_pc_opt) {
    if (this->debug_level >= 2)
        std::cerr << " PMP::vote(...)" << std::endl;
    int n = x.size();
    if (n == 0) {
        if (this->debug_level >= 2)
            std::cerr << "[ PMP::vote] There are no voters." << std::endl;
        return std::vector<int>();
    }
    
    // Safety check: ensure first pattern is not empty
    if (x[0].pattern.empty() || x[0].pattern[0] == 0) {
        return std::vector<int>();
    }

    if (this->debug_level >= 2) {
        std::cerr << "[ PMP::vote] Taking a vote among:" << std::endl;
        for (int i = 0; i < n; i += 1)
            std::cerr << "<" << std::setw(3) << i + 1 << "> " << custom_util::pattern_to_string(x[i].pattern) << std::endl;
    }
    
    int pattern_len = is_pc_opt ? this->pattern_len / PATTERN_DEGRADE_LEVEL : this->pattern_len;
    std::vector<int> res(pattern_len, 0);

    for (int i = 0; i < pattern_len; i += 1) {
        int cnt = 0;
        for (int j = 0; j < n; j += 1) {
            // Bounds check
            if (i < static_cast<int>(x[j].pattern.size())) {
                cnt += x[j].pattern[i];
            }
        }
        double p = 1.0 * cnt / x[0].pattern[0];
        if (p > 1) {
            std::cout << "cnt:" << cnt << ",total:" << x[0].pattern[0] << std::endl;
            p = 1.0;  // Clamp instead of asserting
        }

        if (x[0].pattern[0] <= START_CONF) {
            break;
        }

        // // Adaptive thresholds integration
        // double l1_thresh = is_pc_opt ? adaptive_l1d_thresh : adaptive_l1d_thresh;  // Reuse for PC (or add PC-specific)
        // double l2_thresh = is_pc_opt ? adaptive_l2c_thresh : adaptive_l2c_thresh;

        // if (is_pc_opt) {
            if (p >= adaptive_l1d_thresh)  // Use adaptive thresholding instead of fixed
                res[i] = FILL_L1_PMP;
            else if (p >= adaptive_l2c_thresh) // Use adaptive thresholding instead of fixed
                res[i] = FILL_L2_PMP;
            else if (p >= PC_LLC_THRESH)
                res[i] = FILL_LLC_PMP;
            else
                res[i] = 0;
        // } else {
        //     if (p >= adaptive_l1d_thresh) // Use adaptive thresholding instead of fixed
        //         res[i] = FILL_L1_PMP;
        //     else if (p >= adaptive_l2c_thresh) // Use adaptive thresholding instead of fixed
        //         res[i] = FILL_L2_PMP;
        //     else if (p >= LLC_THRESH)
        //         res[i] = FILL_LLC_PMP;
        //     else
        //         res[i] = 0;
        // }
    }
    if (this->debug_level >= 2) {
        std::cerr << "<res> " << custom_util::pattern_to_string(res) << std::endl;
    }

    return res;
}

void PMP::update_feedback(bool was_useful) {  // was_useful: true if PF hit demand (from ChampSim fill callback)
    if (was_useful) recent_pf_useful++;
    if (++recent_pf_issued % 1000 == 0) {  // 1K PF window
        double acc = recent_pf_issued > 0 ? static_cast<double>(recent_pf_useful) / recent_pf_issued : 0.0;
        if (acc < 0.30) {
            adaptive_l1d_thresh = std::max(0.30, adaptive_l1d_thresh * 0.9);
            adaptive_l2c_thresh = std::max(0.10, adaptive_l2c_thresh * 0.9);
            if (debug_level >= 1) std::cerr << "[PMP] Low acc (" << acc << "): Thresh L1D=" << adaptive_l1d_thresh << std::endl;
        } else if (acc > 0.70) {
            adaptive_l1d_thresh = std::min(0.60, adaptive_l1d_thresh * 1.05);
            adaptive_l2c_thresh = std::min(0.20, adaptive_l2c_thresh * 1.05);
            if (debug_level >= 1) std::cerr << "[PMP] High acc (" << acc << "): Thresh L1D=" << adaptive_l1d_thresh << std::endl;
        }
        pmp_recent_acc = acc;  // Set global for CLIP tie-in
        if (debug_level >= 1) std::cerr << "[PMP-CLIP] Shared acc=" << std::fixed << std::setprecision(3) << acc << std::endl;
        recent_pf_issued = 0;
        recent_pf_issued = recent_pf_useful = 0;
    }
}

double PMP::get_recent_accuracy() const {
    return recent_pf_issued > 0 ? static_cast<double>(recent_pf_useful) / recent_pf_issued : 0.0;
}

} // namespace pmp_enhanced

// ============================================================================
// ChampSim Interface
// ============================================================================

using namespace pmp_enhanced;

void CACHE::prefetcher_initialize() {
    std::cout << NAME << " PMP Enhanced (with CLIP)" << std::endl;
    
    const int PATTERN_LEN = (1 << IN_REGION_BITS) / BLOCK_SIZE;
    const int FT_SIZE = 64, FT_WAY = 8;
    const int AT_SIZE = 32, AT_WAY = 16;
    const int OPT_SIZE = (1 << OFFSET_BITS), OFFSET_MAX_CONF = 32;
    const int PPT_SIZE = (1 << PC_BITS), PC_MAX_CONF = 32;
    const int PF_BUFFER_SIZE = 32, PF_BUFFER_WAY = 8;
    
    prefetchers = std::vector<PMP>(
        NUM_CPUS, PMP(PATTERN_LEN, OFFSET_BITS, OPT_SIZE, OFFSET_MAX_CONF, 1,
                     PC_BITS, PPT_SIZE, PC_MAX_CONF, 1,
                     FT_SIZE, FT_WAY, AT_SIZE, AT_WAY,
                     PF_BUFFER_SIZE, PF_BUFFER_WAY,
                     1, 2, 3, 0, cpu));
}

uint32_t CACHE::prefetcher_cache_operate(uint64_t addr, uint64_t ip, uint8_t cache_hit, 
                                         uint8_t type, uint32_t metadata_in) {
    if (type != LOAD) return metadata_in;
    
    uint64_t block_number = addr >> LOG2_BLOCK_SIZE;
    
    // Corrected stall detection: Use get_occupancy(3, 0) for MSHR occ, get_size(3, 0) for size
    static std::unordered_map<uint64_t, int> consec_misses;  // Per-IP
    static std::unordered_map<uint64_t, uint64_t> last_miss_cycle;
    bool rob_stalled = false;
    bool is_miss = !cache_hit;
    
    if (is_miss) {
        consec_misses[ip]++;
        last_miss_cycle[ip] = current_cycle;
        
        int mshr_occ = get_occupancy(3, 0);
        int mshr_size = get_size(3, 0);
        
        // Only mark as stalled if:
        // 1. High MSHR pressure (>75%) AND multiple consecutive misses
        // 2. OR very high consecutive miss count (>4)
        rob_stalled = ((mshr_occ > mshr_size * 0.75 && consec_misses[ip] >= 3) || 
                       consec_misses[ip] >= 5);
    } else {
        consec_misses[ip] = 0;
    }

    // Train CLIP with corrected stall detection
    prefetchers[cpu].get_clip_filter().process_access(addr, ip, rob_stalled, is_miss);
    
    // PMP access and prefetch
    prefetchers[cpu].access(block_number, ip);
    prefetchers[cpu].prefetch(this, block_number, ip, rob_stalled, cache_hit ? 0 : 1);
    
    return metadata_in;


    // bool rob_stalled = false;
    // bool is_miss = !cache_hit;
    // consec_misses[ip]++;

//     int mshr_occ = get_occupancy(3, 0);  // MSHR occupancy (type 3)
//     int mshr_size = get_size(3, 0);  // MSHR size
//     bool rob_stalled = !cache_hit && (mshr_occ > mshr_size * 0.5 || consec_misses[ip] >= 2);
//     if (cache_hit) consec_misses[ip] = 0;  // Reset on hit
//     uint8_t miss_level = cache_hit ? 0 : (metadata_in & 0xFF);

//     bool is_miss = !cache_hit;

//     // Train CLIP
//     prefetchers[cpu].get_clip_filter().process_access(addr, ip, rob_stalled, is_miss);
    
//     // PMP access and prefetch
//     prefetchers[cpu].access(block_number, ip);
//     prefetchers[cpu].prefetch(this, block_number, ip, rob_stalled, miss_level);
    
//     return metadata_in;
}

// uint32_t CACHE::prefetcher_cache_operate(uint64_t addr, uint64_t ip, uint8_t cache_hit, 
//                                           uint8_t type, uint32_t metadata_in) {
//     if (type != LOAD) return metadata_in;
    
//     uint64_t block_number = addr >> LOG2_BLOCK_SIZE;
//     // uint64_t region_number = block_number >> OFFSET_BITS;
    
//     // bool rob_stalled = false;
//     // if (!cache_hit) {
//     //     consecutive_misses[ip]++;
//     //     // Only consider ROB stalled after multiple consecutive misses
//     //     rob_stalled = (consecutive_misses[ip] >= 3);
//     // } else {
//     //     consecutive_misses[ip] = 0;
//     // }
    
//     // // Estimate ROB stall
//     // bool rob_stalled = false;
//     // if (!cache_hit) {
//     //       rob_stalled = true;
//     // }

//     static std::unordered_map<uint64_t, int> consec_misses;  // Per-IP

//     consec_misses[ip]++;
//     bool rob_stalled = !cache_hit && (MSHR.size() > mshr_size * 0.5 || consec_misses[ip] >= 2);
//     if (cache_hit) consec_misses[ip] = 0;  // Reset on hit
//     // bool rob_stalled = !cache_hit && (get_occupancy(0,0) > get_size(0,0) * 0.9);
//     uint8_t miss_level = cache_hit ? 0 : (metadata_in & 0xFF);

//     // Train CLIP
//     prefetchers[cpu].get_clip_filter().process_access(addr, ip, rob_stalled, miss_level);
    
//     // Track trigger IP
//     // region_trigger_map[region_number] = ip;
    
//     // PMP access and prefetch
//     prefetchers[cpu].access(block_number, ip);
//     prefetchers[cpu].prefetch(this, block_number, ip, rob_stalled, miss_level);
    
//     return metadata_in;
// }

// uint32_t CACHE::prefetcher_cache_fill(uint64_t addr, uint32_t set, uint32_t way, 
//                                        uint8_t prefetch, uint64_t evicted_addr, 
//                                        uint32_t metadata_in) {
//     uint64_t evicted_block_number = evicted_addr >> LOG2_BLOCK_SIZE;
//     if (this->block[set * NUM_WAY + way].valid == 0) return metadata_in;
    
//     for (int i = 0; i < NUM_CPUS; i += 1) {
//         if (!block[set * NUM_WAY + way].prefetch)
//             prefetchers[i].eviction(evicted_block_number);
//     }

//     return metadata_in;
// }

uint32_t CACHE::prefetcher_cache_fill(uint64_t addr, uint32_t set, uint32_t way, 
                                      uint8_t prefetch, uint64_t evicted_addr, 
                                      uint32_t metadata_in) {
   uint64_t evicted_block_number = evicted_addr >> LOG2_BLOCK_SIZE;
    if (this->block[set * NUM_WAY + way].valid == 0) return metadata_in;
    
    // Standard fill update (ChampSim standard)
    this->block[set * NUM_WAY + way].address = addr;
    this->block[set * NUM_WAY + way].prefetch = prefetch;

    // Eviction
    uint64_t evicted_block = evicted_addr >> LOG2_BLOCK_SIZE;
    for (int i = 0; i < NUM_CPUS; ++i) {
        if (evicted_addr && !block[set * NUM_WAY + way].prefetch) {
            prefetchers[i].eviction(evicted_block);
        }
    }

    // Usefulness feedback
    if (prefetch) {
        prefetchers[cpu].update_feedback(true);
    }

    return metadata_in;
}

void CACHE::prefetcher_cycle_operate() {}

void CACHE::prefetcher_final_stats() {
    std::cout << "\n=== PMP Statistics ===" << std::endl;
    std::cout << "Prefetch to L1: " << prefetch_to_l1 << std::endl;
    std::cout << "Prefetch to L2: " << prefetch_to_l2 << std::endl;
    std::cout << "Invalid by Eviction: " << prefetchers[cpu].invalid_by_eviction << std::endl;
    std::cout << "Invalid by Max: " << prefetchers[cpu].invalid_by_max << std::endl;
    
    prefetchers[cpu].get_clip_filter().print_stats();

    // DEBUG STATEMENTS
     std::cout << "\n=== CLIP-PMP Integration Diagnostics ===" << std::endl;
    auto& clip = prefetchers[cpu].get_clip_filter();
    auto& pmp = prefetchers[cpu];
    const auto& crit_filter = clip.get_crit_filter();
    
    // Analyze critical IPs
    int total_critical_ips = 0;
    int critical_accurate_ips = 0;
    int critical_with_issues = 0;
    int critical_without_issues = 0;
    
    uint64_t total_issues = 0;
    uint64_t total_hits = 0;
    
    std::vector<std::tuple<uint64_t, uint8_t, uint8_t, uint8_t, double>> critical_ip_details;
    
    for (const auto& [ip, entry] : crit_filter) {
        if (entry.crit_count >= 4) {  // Critical threshold
            total_critical_ips++;
            
            if (entry.is_critical_and_accurate()) {
                critical_accurate_ips++;
            }
            
            if (entry.issue_count > 0) {
                critical_with_issues++;
            } else {
                critical_without_issues++;
            }
            
            total_issues += entry.issue_count;
            total_hits += entry.hit_count;
            
            // Store for detailed analysis
            double accuracy = entry.get_accuracy();
            critical_ip_details.push_back(
                std::make_tuple(ip, entry.crit_count, entry.issue_count, 
                               entry.hit_count, accuracy)
            );
        }
    }
    
    std::cout << "Total IPs tracked by CLIP: " << crit_filter.size() << std::endl;
    std::cout << "Critical IPs (crit >= 4): " << total_critical_ips << std::endl;
    std::cout << "Critical AND accurate IPs: " << critical_accurate_ips << std::endl;
    std::cout << "Critical IPs with prefetches issued: " << critical_with_issues << std::endl;
    std::cout << "Critical IPs WITHOUT prefetches: " << critical_without_issues << std::endl;
    
    if (total_critical_ips > 0) {
        std::cout << "Average issues per critical IP: " 
                  << (double)total_issues / total_critical_ips << std::endl;
        std::cout << "Average hits per critical IP: " 
                  << (double)total_hits / total_critical_ips << std::endl;
    }
    
    // Pattern buffer analysis
    int pattern_buffer_entries = pmp.get_pattern_buffer_size();
    std::cout << "\nPMP Pattern Buffer Usage: " << pattern_buffer_entries 
              << " entries" << std::endl;
    
    // Detailed critical IP analysis
    if (!critical_ip_details.empty()) {
        std::cout << "\n=== Critical IPs Detailed Analysis ===" << std::endl;
        
        // Sort by criticality count
        std::sort(critical_ip_details.begin(), critical_ip_details.end(),
                  [](const auto& a, const auto& b) {
                      return std::get<1>(a) > std::get<1>(b);
                  });
        
        std::cout << std::setw(8) << "IP" 
                  << std::setw(10) << "Crit" 
                  << std::setw(10) << "Issues"
                  << std::setw(10) << "Hits"
                  << std::setw(12) << "Accuracy"
                  << std::setw(12) << "Status" << std::endl;
        std::cout << std::string(62, '-') << std::endl;
        
        int shown = 0;
        for (const auto& [ip, crit, issues, hits, acc] : critical_ip_details) {
            if (shown++ >= 15) break;  // Show top 15
            
            std::string status;
            if (issues == 0) {
                status = "NO-PREFETCH";
            } else if (acc >= 0.90 && crit >= 4) {
                status = "ACTIVE";
            } else if (acc < 0.90) {
                status = "LOW-ACC";
            } else {
                status = "LOW-CRIT";
            }
            
            std::cout << "0x" << std::hex << std::setw(6) << ip << std::dec
                      << std::setw(10) << (int)crit
                      << std::setw(10) << (int)issues
                      << std::setw(10) << (int)hits
                      << std::setw(12) << std::fixed << std::setprecision(3) << acc
                      << std::setw(12) << status << std::endl;
        }
    }
    
    // CLIP filtering effectiveness
    std::cout << "\n=== CLIP Filtering Effectiveness ===" << std::endl;
    uint64_t total_candidates = clip.get_total_prefetches();
    uint64_t dropped = clip.get_dropped_prefetches();
    uint64_t issued = total_candidates - dropped;
    
    double drop_rate = 0.0;
    double issue_rate = 0.0;

    if (total_candidates > 0) {
        drop_rate = 100.0 * dropped / total_candidates;
        issue_rate = 100.0 * issued / total_candidates;
        
        std::cout << "Total prefetch candidates: " << total_candidates << std::endl;
        std::cout << "Dropped by CLIP: " << dropped 
                  << " (" << std::fixed << std::setprecision(2) << drop_rate << "%)" << std::endl;
        std::cout << "Issued after filtering: " << issued 
                  << " (" << std::fixed << std::setprecision(2) << issue_rate << "%)" << std::endl;
    }
    
    // Sanity checks
    std::cout << "\n=== Sanity Checks ===" << std::endl;
    
    if (total_candidates > 100000000) {
        std::cout << "⚠️  WARNING: Abnormally high prefetch candidates (" 
                  << total_candidates << ")" << std::endl;
        std::cout << "    Expected range: 1M-10M for 100M instructions" << std::endl;
    }
    
    if (critical_without_issues > critical_with_issues) {
        std::cout << "⚠️  WARNING: More critical IPs without prefetches than with" << std::endl;
        std::cout << "    This suggests PMP is not generating patterns for critical IPs" << std::endl;
    }
    
    if (drop_rate < 10.0 && total_candidates > 1000000) {
        std::cout << "⚠️  WARNING: Very low CLIP drop rate (" << drop_rate << "%)" << std::endl;
        std::cout << "    CLIP should be more selective in bandwidth-constrained scenarios" << std::endl;
    }
    
    if (critical_accurate_ips == 0 && total_critical_ips > 5) {
        std::cout << "⚠️  WARNING: No critical AND accurate IPs found" << std::endl;
        std::cout << "    Check if prefetches are being recorded correctly" << std::endl;
    }
    
    std::cout << std::endl;
    // DEBUG STATEMENTS ENDED




    prefetchers[cpu].log();
    
    std::cout << "Filter by PPT: " << filter_by_ppt << std::endl;
}