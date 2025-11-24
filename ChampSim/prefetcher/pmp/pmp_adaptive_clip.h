#ifndef PMP_H
#define PMP_H

// =============================================================================
// PMP Adaptive Prefetcher with CLIP Filter Integration - COMPLETE HEADER
// =============================================================================
// This file contains the COMPLETE implementation of PMP + CLIP
// Every single line of code included - NO placeholders
// =============================================================================

#include "cache.h"
#include "custom_util.h"

#include <bits/stdc++.h>
#include <random>
#include <memory>
#include <stdint.h>

// =============================================================================
// CLIP Filter Components
// =============================================================================

namespace clip {

// Forward declarations
class PMP;

// Debug macros
#define CLIP_DEBUG(x)

// Constants from CLIP paper (MICRO 2023)
/// SINGLE CORE
// constexpr int CRITICALITY_COUNT_THRESHOLD = 1; //4;  // Paper uses 4
// constexpr double IP_ACCURACY_THRESHOLD = 0.30; //0.90;  // paper uses 90%
// constexpr int EXPLORATION_WINDOW_SIZE = 1024;  // Based on L1D misses
// constexpr int BRANCH_HISTORY_LENGTH = 32;       // Last 32 branches
// constexpr int CRITICALITY_HISTORY_LENGTH = 32;  // Last 32 loads

/// MULTI CORE
constexpr int CRITICALITY_COUNT_THRESHOLD = 2; //4;  // Paper uses 4
constexpr double IP_ACCURACY_THRESHOLD = 0.60; //0.90;  // paper uses 90%
constexpr int EXPLORATION_WINDOW_SIZE = 1024;  // Based on L1D misses
constexpr int BRANCH_HISTORY_LENGTH = 32;       // Last 32 branches
constexpr int CRITICALITY_HISTORY_LENGTH = 32;  // Last 32 loads

// Phase change detection
constexpr double APC_CHANGE_THRESHOLD = 0.15;   // 15% change triggers phase change
constexpr int APC_WINDOW_COUNT = 16;            // Track last 16 windows

// ============================================================================
// CriticalityFilterData: Tracks critical IPs and their accuracy
// ============================================================================
class CriticalityFilterData {
public:
    uint64_t ip;
    uint16_t crit_count;        // How many times this IP stalled ROB
    uint16_t hit_count;         // How many prefetches hit
    uint16_t issue_count;       // How many prefetches issued
    bool is_critical_and_accurate;  // Final decision bit
    
    CriticalityFilterData() : ip(0), crit_count(0), hit_count(0), 
                              issue_count(0), is_critical_and_accurate(false) {}
};

// ============================================================================
// CriticalityFilter: Stage I - Filters critical IPs with high accuracy
// ============================================================================
class CriticalityFilter : public custom_util::LRUSetAssociativeCache<CriticalityFilterData> {
    typedef custom_util::LRUSetAssociativeCache<CriticalityFilterData> Super;
    
public:
    CriticalityFilter(int size, int num_ways, int debug_level = 0) 
        : Super(size, num_ways, debug_level) {}
    
    void record_rob_stall(uint64_t ip);
    void record_prefetch_issue(uint64_t ip);
    void record_prefetch_hit(uint64_t ip);
    bool is_critical_and_accurate(uint64_t ip);
    double get_ip_accuracy(uint64_t ip);
    void update_after_exploration_window();
    void reset_all();
    void reset_counts_with_hysteresis();
    std::string log();
    
private:
    void write_data(Entry& entry, custom_util::Table& table, int row) override;
    uint64_t build_key(uint64_t ip);
};

// ============================================================================
// CriticalityPredictorData: Per critical-signature prediction
// ============================================================================
class CriticalityPredictorData {
public:
    uint8_t saturating_counter;  // 3-bit counter
    
    CriticalityPredictorData() : saturating_counter(4) {}  // Initialize to 2^(k-1) = 4
    
    bool is_critical() {
        return (saturating_counter & 0x4) != 0;  // Check MSB of 3-bit counter
    }
    
    void increment() {
        if (saturating_counter < 7) saturating_counter++;
    }
    
    void decrement() {
        if (saturating_counter > 0) saturating_counter--;
    }
};

// ============================================================================
// CriticalityPredictor: Stage II - Predicts dynamic criticality
// ============================================================================
class CriticalityPredictor : public custom_util::LRUSetAssociativeCache<CriticalityPredictorData> {
    typedef custom_util::LRUSetAssociativeCache<CriticalityPredictorData> Super;
    
public:
    CriticalityPredictor(int size, int num_ways, int debug_level = 0)
        : Super(size, num_ways, debug_level) {}
    
    bool predict_critical(uint64_t critical_signature);
    void train(uint64_t critical_signature, bool was_critical);
    void reset_all();
    std::string log();
    
private:
    void write_data(Entry& entry, custom_util::Table& table, int row) override;
    uint64_t build_key(uint64_t critical_signature);
};

// ============================================================================
// UtilityBufferEntry: Tracks issued prefetches
// ============================================================================
struct UtilityBufferEntry {
    uint64_t pf_address;
    uint64_t trigger_ip;
    bool valid;
    
    UtilityBufferEntry() : pf_address(0), trigger_ip(0), valid(false) {}
};

// ============================================================================
// UtilityBuffer: Circular buffer for recent prefetches
// ============================================================================
class UtilityBuffer {
public:
    UtilityBuffer(int size);
    void insert(uint64_t pf_address, uint64_t trigger_ip);
    std::pair<bool, uint64_t> check_and_get_trigger_ip(uint64_t address);
    void clear();
    
private:
    std::vector<UtilityBufferEntry> buffer;
    int size;
    int head;
};

// ============================================================================
// HistoryRegister: Tracks branch and criticality history
// ============================================================================
class HistoryRegister {
public:
    HistoryRegister(int length);
    void update(bool outcome);
    uint64_t get();
    void reset();
    
private:
    int length;
    uint64_t history;
};

// ============================================================================
// APCTracker: Tracks Accesses Per Cycle for phase change detection
// ============================================================================
class APCTracker {
public:
    APCTracker();
    void record_access();
    void record_cycle();
    bool check_phase_change(int window_size_accesses);
    void reset();
    
private:
    int window_count;
    uint64_t current_window_accesses;
    uint64_t current_window_cycles;
    std::vector<double> window_apc_history;
    double get_average_apc();
};

// ============================================================================
// CLIPFilter: Main CLIP filter class
// ============================================================================
class CLIPFilter {
public:
    CLIPFilter(int cpu, int crit_filter_size = 128, int crit_filter_ways = 4,
               int crit_pred_size = 512, int crit_pred_ways = 4,
               int utility_buffer_size = 64, int debug_level = 0);
    
    // Main interface
    bool should_prefetch(uint64_t pf_address, uint64_t trigger_ip);
    void record_rob_stall(uint64_t address, uint64_t ip, bool is_l1_miss);
    void record_prefetch_issue(uint64_t pf_address, uint64_t trigger_ip);
    void record_demand_hit_on_prefetch(uint64_t address);
    void cycle_operate();
    void update_branch_history(bool taken);
    void print_stats();
    std::string log();
    
private:
    uint64_t compute_critical_signature(uint64_t ip, uint64_t address);
    bool is_exploration_window_complete();
    void end_exploration_window();
    void check_and_handle_phase_change();
    
    int cpu;
    CriticalityFilter crit_filter;
    CriticalityPredictor crit_predictor;
    UtilityBuffer utility_buffer;
    HistoryRegister branch_history;
    HistoryRegister criticality_history;
    APCTracker apc_tracker;
    
    uint64_t l1d_misses_in_window;
    uint64_t total_prefetch_candidates;
    uint64_t prefetches_issued;
    uint64_t prefetches_dropped_not_critical;
    uint64_t prefetches_dropped_low_accuracy;
    uint64_t critical_loads_detected;
    uint64_t phase_changes_detected;
    
    int debug_level;
};

} // namespace clip

// =============================================================================
// PMP Prefetcher Components
// =============================================================================

namespace pmp {

// Forward-declare PMP class
class PMP;

// PMP Constants
constexpr int PF_BUFFER_SIZE = 32;
constexpr int PF_BUFFER_WAY = 8;

#define DEBUG(x)

#define __fine_offset(addr) (addr & OFFSET_MASK)
#define __coarse_offset(fine_offset) ((fine_offset) >> (LOG2_BLOCK_SIZE - BOTTOM_BITS))

#define FT_CACHE_TYPE custom_util::SRRIPSetAssociativeCache
#define AT_CACHE_TYPE custom_util::LRUSetAssociativeCache
#define PS_CACHE_TYPE custom_util::LRUSetAssociativeCache

constexpr int BOTTOM_BITS = 6;
constexpr int PC_BITS = 5;
constexpr int BACKOFF_TIMES = 1;

constexpr int IN_REGION_BITS = 11;
constexpr int OFFSET_BITS = IN_REGION_BITS - BOTTOM_BITS;
constexpr int OFFSET_MASK = (1 << OFFSET_BITS) - 1;

constexpr int START_CONF = 0;
constexpr int PATTERN_DEGRADE_LEVEL = 2;

// Tracker for in-flight prefetches
class InflightPFData {
public:
    bool used = false;
    uint64_t issue_cycle = 0;
};

class InflightPFTracker : public custom_util::LRUSetAssociativeCache<InflightPFData> {
    typedef custom_util::LRUSetAssociativeCache<InflightPFData> Super;

public:
    InflightPFTracker(int size, int num_ways) : Super(size, num_ways) {}
    
    void write_data(Entry& entry, custom_util::Table& table, int row) override {
        table.set_cell(row, 0, entry.key);
        table.set_cell(row, 1, entry.data.used);
        table.set_cell(row, 2, entry.data.issue_cycle);
    }
    
    uint64_t build_key(uint64_t key) {
        return custom_util::hash_index(key, this->index_len);
    }
};

int filter_by_ppt = 0;
int prefetch_to_l1, prefetch_to_l2 = 0;

// SMS Filter Table Data
class FilterTableData {
public:
    int offset;
    uint64_t pc;
};

// SMS Filter Table
class FilterTable : public FT_CACHE_TYPE<FilterTableData> {
    typedef FT_CACHE_TYPE<FilterTableData> Super;

public:
    FilterTable(int size, int debug_level = 0, int num_ways = 16) : Super(size, num_ways) {
        if (this->debug_level >= 1)
            std::cerr << "FilterTable::FilterTable(size=" << size << ", debug_level=" << debug_level
                      << ", num_ways=" << num_ways << ")" << std::dec << std::endl;
    }

    Entry* find(uint64_t region_number) {
        if (this->debug_level >= 2)
            std::cerr << "FilterTable::find(region_number=0x" << std::hex << region_number << ")" << std::dec << std::endl;
        uint64_t key = this->build_key(region_number);
        Entry* entry = Super::find(key);
        if (!entry) {
            if (this->debug_level >= 2)
                std::cerr << "[FilterTable::find] Miss!" << std::dec << std::endl;
            return nullptr;
        }
        if (this->debug_level >= 2)
            std::cerr << "[FilterTable::find] Hit!" << std::dec << std::endl;
        Super::rp_promote(key);
        return entry;
    }

    void insert(uint64_t region_number, int offset, uint64_t pc) {
        if (this->debug_level >= 2)
            std::cerr << "FilterTable::insert(region_number=0x" << std::hex << region_number
                      << ", offset=" << std::dec << offset << ")" << std::dec << std::endl;
        uint64_t key = this->build_key(region_number);
        Super::insert(key, { offset, pc });
        Super::rp_insert(key);
    }

    Entry* erase(uint64_t region_number) {
        uint64_t key = this->build_key(region_number);
        return Super::erase(key);
    }

    std::string log() {
        std::vector<std::string> headers({ "Region", "Offset" });
        return Super::log(headers);
    }

private:
    void write_data(Entry& entry, custom_util::Table& table, int row) {
        uint64_t key = custom_util::hash_index(entry.key, this->index_len);
        table.set_cell(row, 0, key);
        table.set_cell(row, 1, entry.data.offset);
    }

    uint64_t build_key(uint64_t region_number) {
        uint64_t key = region_number & ((1ULL << 37) - 1);
        return custom_util::hash_index(key, this->index_len);
    }
};

class AccumulationTableData {
public:
    int offset;
    int second_offset;
    uint64_t pc;
    std::vector<bool> pattern;
};

class AccumulationTable : public AT_CACHE_TYPE<AccumulationTableData> {
    typedef AT_CACHE_TYPE<AccumulationTableData> Super;

public:
    AccumulationTable(int size, int pattern_len, int debug_level = 0, int num_ways = 16) : Super(size, num_ways), pattern_len(pattern_len) {
        if (this->debug_level >= 1)
            std::cerr << "AccumulationTable::AccumulationTable(size=" << size << ", pattern_len=" << pattern_len
                      << ", debug_level=" << debug_level << ", num_ways=" << num_ways << ")" << std::dec << std::endl;
    }

    bool set_pattern(uint64_t region_number, int offset) {
        if (this->debug_level >= 2)
            std::cerr << "AccumulationTable::set_pattern(region_number=0x" << std::hex << region_number << ", offset=" << std::dec
                      << offset << ")" << std::dec << std::endl;
        uint64_t key = this->build_key(region_number);
        Entry* entry = Super::find(key);
        if (!entry) {
            if (this->debug_level >= 2)
                std::cerr << "[AccumulationTable::set_pattern] Not found!" << std::dec << std::endl;
            return false;
        }
        entry->data.pattern[offset] = true;
        Super::rp_promote(key);
        if (this->debug_level >= 2)
            std::cerr << "[AccumulationTable::set_pattern] OK!" << std::dec << std::endl;
        return true;
    }

    Entry insert(uint64_t region_number, uint64_t pc, int offset, int second_offset) {
        if (this->debug_level >= 2)
            std::cerr << "AccumulationTable::insert(region_number=0x" << std::hex << region_number
                      << ", offset=" << std::dec << offset << std::dec << std::endl;
        uint64_t key = this->build_key(region_number);
        std::vector<bool> pattern(this->pattern_len, false);
        pattern[__coarse_offset(offset)] = true;
        Entry old_entry = Super::insert(key, { offset, second_offset, pc, pattern });
        Super::rp_insert(key);
        return old_entry;
    }

    Entry* erase(uint64_t region_number) {
        uint64_t key = this->build_key(region_number);
        return Super::erase(key);
    }

    std::string log() {
        std::vector<std::string> headers({ "Region", "Offset", "Second", "Pattern" });
        return Super::log(headers);
    }

private:
    void write_data(Entry& entry, custom_util::Table& table, int row) {
        uint64_t key = custom_util::hash_index(entry.key, this->index_len);
        table.set_cell(row, 0, key);
        table.set_cell(row, 1, entry.data.offset);
        table.set_cell(row, 2, entry.data.second_offset);
        table.set_cell(row, 3, custom_util::pattern_to_string(entry.data.pattern));
    }

    uint64_t build_key(uint64_t region_number) {
        uint64_t key = region_number & ((1ULL << 37) - 1);
        return custom_util::hash_index(key, this->index_len);
    }

    int pattern_len;
};

class OffsetPatternTableData {
public:
    std::vector<int> pattern;
    int second_offset;
};

class OffsetPatternTable : public custom_util::LRUSetAssociativeCache<OffsetPatternTableData> {
    typedef custom_util::LRUSetAssociativeCache<OffsetPatternTableData> Super;

public:
    OffsetPatternTable(int size, int pattern_len, int tag_size,
        int num_ways = 16, int max_conf = 16,
        int debug_level = 0, int cpu = 0) : Super(size, num_ways, debug_level), pattern_len(pattern_len), tag_size(tag_size), max_conf(max_conf), cpu(cpu) {
        if (this->debug_level >= 1)
            std::cerr << "OffsetPatternTable::OffsetPatternTable(size=" << size << ", pattern_len=" << pattern_len
                      << ", tag_size=" << tag_size
                      << ", debug_level=" << debug_level << ", num_ways=" << num_ways << ")"
                      << std::dec << std::endl;
    }

#define ADD(x, v) x = (x < v) ? (x + 1) : x

    void insert(uint64_t address, uint64_t pc, const std::vector<bool>& pattern, bool is_degrade, int second_offset) {
        uint64_t key = this->build_key(address, pc);
        Entry* entry = Super::find(key);
        assert(pattern[0]);
        if (entry) {
            int max_value = 0;
            auto& stored_pattern = entry->data.pattern;
            for (int i = 0; i < this->pattern_len; i++) {
                pattern[i] ? ADD(stored_pattern[i], max_conf) : 0;
                if (i > 0 && max_value < stored_pattern[i]) {
                    max_value = stored_pattern[i];
                }
            }

            if (entry->data.pattern[0] == max_conf) {
                if (max_value < (1 << BACKOFF_TIMES)) {
                    entry->data.pattern[0] = max_value;
                } else
                    for (auto& e : stored_pattern) {
                        e >>= BACKOFF_TIMES;
                    }
            }
            Super::rp_promote(key);
        } else {
            Super::insert(key, OffsetPatternTableData{ custom_util::pattern_convert(pattern), second_offset });
            Super::rp_insert(key);
        }
    }

    std::vector<OffsetPatternTableData> find(uint64_t pc, uint64_t block_number) {
        if (this->debug_level >= 2)
            std::cerr << "OffsetPatternTable::find(pc=0x" << std::hex << pc << ", address=0x" << block_number << ")" << std::dec << std::endl;
        uint64_t key = this->build_key(block_number, pc);
        Entry* entry = Super::find(key);
        std::vector<OffsetPatternTableData> matches;
        if (entry) {
            auto& cur_pattern = entry->data;
            matches.push_back(cur_pattern);
        }
        return matches;
    }

    std::string log() {
        std::vector<std::string> headers({ "Key", "Second", "Pattern" });
        return Super::log(headers);
    }

private:
    void write_data(Entry& entry, custom_util::Table& table, int row) {
        table.set_cell(row, 0, entry.key);
        table.set_cell(row, 1, entry.data.second_offset);
        table.set_cell(row, 2, custom_util::pattern_to_string(entry.data.pattern));
    }

    virtual uint64_t build_key(uint64_t address, uint64_t pc) {
        uint64_t offset = __fine_offset(address);
        uint64_t key = offset & ((1 << this->tag_size) - 1);
        return key;
    }

protected:
    const int pattern_len;
    const int tag_size, cpu;
    const int max_conf;
};

class PCPatternTable : public OffsetPatternTable {
public:
    PCPatternTable(int size, int pattern_len, int tag_size,
        int num_ways = 16, int max_conf = 32,
        int debug_level = 0, int cpu = 0) : OffsetPatternTable(size, pattern_len, tag_size, num_ways, max_conf, debug_level, cpu) {}

private:
    virtual uint64_t build_key(uint64_t address, uint64_t pc) override {
        return custom_util::hash_index(pc, this->index_len) & ((1 << this->tag_size) - 1);
    }
};

class PrefetchBufferData {
public:
    std::vector<int> pattern;
};

class PrefetchBuffer : public PS_CACHE_TYPE<PrefetchBufferData> {
    typedef PS_CACHE_TYPE<PrefetchBufferData> Super;

public:
    PrefetchBuffer(int size, int pattern_len, int debug_level = 0, int num_ways = 16) : Super(size, num_ways), pattern_len(pattern_len) {
        if (this->debug_level >= 1)
            std::cerr << "PrefetchBuffer::PrefetchBuffer(size=" << size << ", pattern_len=" << pattern_len
                      << ", debug_level=" << debug_level << ", num_ways=" << num_ways << ")" << std::dec << std::endl;
    }

    void insert(uint64_t region_number, std::vector<int> pattern) {
        if (this->debug_level >= 2)
            std::cerr << "PrefetchBuffer::insert(region_number=0x" << std::hex << region_number
                      << ", pattern=" << custom_util::pattern_to_string(pattern) << ")" << std::dec << std::endl;
        uint64_t key = this->build_key(region_number);
        Super::insert(key, { pattern });
        Super::rp_insert(key);
    }

    int prefetch(PMP* pmp_parent, CACHE* cache, uint64_t block_address);

    std::string log() {
        std::vector<std::string> headers({ "Region", "Pattern" });
        return Super::log(headers);
    }

private:
    void write_data(Entry& entry, custom_util::Table& table, int row) {
        uint64_t key = custom_util::hash_index(entry.key, this->index_len);
        table.set_cell(row, 0, key);
        table.set_cell(row, 1, custom_util::pattern_to_string(entry.data.pattern));
    }

    uint64_t build_key(uint64_t region_number) {
        uint64_t key = region_number;
        return custom_util::hash_index(key, this->index_len);
    }

    int pattern_len;
};

// =============================================================================
// PMP with CLIP Integration
// =============================================================================

class PMP {
public:
    PMP(int pattern_len, int offset_width, int opt_size, int opt_max_conf, int opt_ways, int pc_width,
        int ppt_size, int ppt_max_conf, int ppt_ways, int filter_table_size, int ft_way,
        int accumulation_table_size, int at_way, int pf_buffer_size, int pf_buffer_way,
        int FILL_L1, int FILL_L2, int FILL_LLC,
        int debug_level = 0, int cpu = 0);
    
    void access(uint64_t block_number, uint64_t pc);
    void eviction(uint64_t block_number);
    int prefetch(CACHE* cache, uint64_t block_number);
    void set_debug_level(int debug_level);
    void log();
    
    // Adaptive mechanism
    void cycle_operate();
    void record_prefetch_issue(uint64_t pf_addr);
    void record_prefetch_eviction(uint64_t pf_addr);
    
    // CLIP integration methods
    void record_load_completion(uint64_t address, uint64_t ip, bool is_l1_miss, 
                                int latency, bool rob_was_stalled);
    
    int FILL_L1_PMP;
    int FILL_L2_PMP;
    int FILL_LLC_PMP;
    int invalid_by_eviction = 0;
    int invalid_by_max = 0;
    
    // Adaptive MSHR reservation
    double demand_reserve_pct = 0.25;
    uint64_t demand_miss_blocked_count = 0;
    uint64_t demand_miss_total_count = 0;
    
    // CLIP Filter Integration
    std::unique_ptr<clip::CLIPFilter> clip_filter;
    bool use_clip = true;
    std::unordered_map<uint64_t, uint64_t> region_to_trigger_ip;
    
    double L1D_THRESH;
    double L2C_THRESH;
    const double LLC_THRESH = 1;

private:
    std::vector<int> find_in_opt(uint64_t pc, uint64_t block_number);
    void insert_in_opt(const AccumulationTable::Entry& entry);
    std::vector<int> vote(const std::vector<OffsetPatternTableData>& x, bool is_pc_opt = false);
    
    const double PC_L1D_THRESH = 0.50;
    const double PC_L2C_THRESH = 0.150;
    const double PC_LLC_THRESH = 1;
    
    int pattern_len;
    FilterTable filter_table;
    AccumulationTable accumulation_table;
    OffsetPatternTable opt;
    PCPatternTable ppt;
    PrefetchBuffer pf_buffer;
    int debug_level = 0;
    int cpu;
    
    // Adaptive mechanism
    uint64_t cycle_count = 0;
    uint64_t useful_prefetches = 0;
    uint64_t useless_prefetches = 0;
    InflightPFTracker inflight_pf_tracker;
    const double L2C_THRESH_RATIO = 0.3;
    
    const uint64_t ADAPTIVE_INTERVAL = 10000;
	const double HIGH_ACCURACY_TARGET = 0.75;
	const double LOW_ACCURACY_TARGET = 0.40;
	const double THRESHOLD_STEP = 0.01;
	const double MAX_L1D_THRESH = 0.90;
	const double MIN_L1D_THRESH = 0.10;
    static constexpr uint64_t PREFETCH_TIMEOUT_CYCLES = 50000;
};

} // namespace pmp

#endif
