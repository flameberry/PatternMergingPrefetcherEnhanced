#ifndef PMP_ENHANCED_H
#define PMP_ENHANCED_H

#include "custom_util.h"
#include "cache.h"

#include <stdint.h>
#include <bits/stdc++.h>
#include <random>
#include <deque>

namespace pmp_enhanced {

#define DEBUG(x)

// #define __fine_offset(addr) (addr & OFFSET_MASK)
// #define __coarse_offset(fine_offset) ((fine_offset) >> (LOG2_BLOCK_SIZE - BOTTOM_BITS))

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

// Global counters
extern int filter_by_ppt;
extern int prefetch_to_l1, prefetch_to_l2;

inline constexpr int fine_offset(uint64_t addr) {
    return addr & OFFSET_MASK;
}

inline constexpr int coarse_offset(int m_fine_offset) {
    return m_fine_offset >> (LOG2_BLOCK_SIZE - BOTTOM_BITS);
}

// ============================================================================
// CLIP Configuration and Structures
// ============================================================================

namespace clip {

constexpr int CRIT_COUNT_THRESHOLD = 4;
// constexpr double PER_IP_ACCURACY_THRESHOLD = 0.90;
constexpr int UTILITY_BUF_SIZE = 256;
constexpr int EXPLORATION_WINDOW = 1024;
constexpr int MAX_PREDICTOR_ENTRIES = 512;
constexpr int MAX_FILTER_ENTRIES = 128;

struct CriticalityEntry {
    uint8_t crit_count = 0;
    uint8_t hit_count = 0;
    uint8_t issue_count = 0;
    
    double get_accuracy() const {
        return (issue_count > 0) ? static_cast<double>(hit_count) / issue_count : 0.0;
    }
    
    bool is_critical_and_accurate() const {
        // More lenient thresholds
        if (crit_count < 2) return false;  // 4 critical event
        if (issue_count < 16) return false; // Need history
        if (crit_count >= 2) {
        return get_accuracy() >= 0.15;     // Match your critical threshold
        } else {
            return get_accuracy() >= 0.25;     // Match your non-critical threshold
        }
        // return get_accuracy() >= 0.50;     // 90% accuracy threshold
    }
};

struct UtilityEntry {
    uint64_t ip_tag = 0;
    uint64_t pf_line = 0;
    bool valid = false;
};

class CLIPFilter {
public:
    CLIPFilter(int cpu_id = 0);
    
    void process_access(uint64_t addr, uint64_t ip, bool rob_stalled, bool is_miss);
    bool should_issue_prefetch(uint64_t pf_addr, uint64_t trigger_ip);
    void record_prefetch_issue(uint64_t pf_addr, uint64_t trigger_ip);
    void print_stats() const;
    
    void enable(bool e) { enabled_ = e; }
    bool is_enabled() const { return enabled_; }

    // ADD THESE METHODS FOR DIAGNOSTICS
    const std::unordered_map<uint64_t, CriticalityEntry>& get_crit_filter() const {
        return crit_filter_;
    }
    
    int get_total_prefetches() const { return total_prefetches_; }
    int get_dropped_prefetches() const { return dropped_prefetches_; }

     // ADD THESE METHODS FOR DIAGNOSTICS ENDS
    
    
private:
    static uint64_t get_ip_tag(uint64_t ip) { return ip & 0x3F; }
    uint64_t build_signature(uint64_t ip, uint64_t addr) const;
    void update_on_stall(uint64_t ip);
    void check_utility(uint64_t demand_addr);
    void reset_exploration_window();
    void print_top_ips(int count) const;
    
    int cpu_id_;
    std::unordered_map<uint64_t, CriticalityEntry> crit_filter_;
    std::unordered_map<uint64_t, uint8_t> crit_predictor_;
    
    // Replace deque with unordered_map for O(1) lookup
    std::unordered_map<uint64_t, std::pair<uint64_t, bool>> utility_map_; // pf_line -> (ip_tag, valid)
    std::deque<uint64_t> utility_order_; // FIFO ordering

    std::deque<UtilityEntry> utility_buffer_;
    uint32_t criticality_history_;
    uint64_t exploration_miss_count_;
    uint64_t total_prefetches_;
    uint64_t dropped_prefetches_;
    bool enabled_;

    int exploration_windows_completed_ = 0;
    bool in_exploration_phase_ = true;  
};

} // namespace clip

// ============================================================================
// Original PMP Structures
// ============================================================================

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
    FilterTable(int size, int debug_level = 0, int num_ways = 16) :
        Super(size, num_ways) {
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
        Super::insert(key, {offset, pc});
        Super::rp_insert(key);
    }

    Entry* erase(uint64_t region_number) {
        uint64_t key = this->build_key(region_number);
        return Super::erase(key);
    }

    std::string log() {
        std::vector<std::string> headers({"Region", "Offset"});
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
    AccumulationTable(int size, int pattern_len, int debug_level = 0, int num_ways = 16) :
        Super(size, num_ways), pattern_len(pattern_len) {
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
        pattern[coarse_offset(offset)] = true;
        Entry old_entry = Super::insert(key, {offset, second_offset, pc, pattern});
        Super::rp_insert(key);
        return old_entry;
    }

    Entry* erase(uint64_t region_number) {
        uint64_t key = this->build_key(region_number);
        return Super::erase(key);
    }

    std::string log() {
        std::vector<std::string> headers({"Region", "Offset", "Second", "Pattern"});
        return Super::log(headers);
    }

    int get_index_len() const { return this->index_len; }

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
                       int debug_level = 0, int cpu = 0) :
        Super(size, num_ways, debug_level),
        pattern_len(pattern_len), tag_size(tag_size),
        max_conf(max_conf), cpu(cpu) {
        if (this->debug_level >= 1)
            std::cerr << "OffsetPatternTable::OffsetPatternTable(size=" << size << ", pattern_len=" << pattern_len
                      << ", tag_size=" << tag_size
                      << ", debug_level=" << debug_level << ", num_ways=" << num_ways << ")"
                      << std::dec << std::endl;
    }

    void insert(uint64_t address, uint64_t pc, std::vector<bool> pattern, bool is_degrade, int second_offset) {
        if (this->debug_level >= 2)
            std::cerr << "OffsetPatternTable::insert(" << std::hex << "address=0x" << address
                      << ", pattern=" << custom_util::pattern_to_string(pattern) << ")" << std::dec << std::endl;
        int offset = coarse_offset(fine_offset(address));
        offset = is_degrade ? offset / PATTERN_DEGRADE_LEVEL : offset;
        pattern = custom_util::my_rotate(pattern, -offset);
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
            Super::insert(key, OffsetPatternTableData{custom_util::pattern_convert(pattern), second_offset});
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
        std::vector<std::string> headers({"Key", "Second", "Pattern"});
        return Super::log(headers);
    }

protected:
    virtual uint64_t build_key(uint64_t address, uint64_t pc) {
        uint64_t offset = fine_offset(address);
        uint64_t key = offset & ((1 << this->tag_size) - 1);
        return key;
    }

    void write_data(Entry& entry, custom_util::Table& table, int row) {
        table.set_cell(row, 0, entry.key);
        table.set_cell(row, 1, entry.data.second_offset);
        table.set_cell(row, 2, custom_util::pattern_to_string(entry.data.pattern));
    }

    const int pattern_len;
    const int tag_size, cpu;
    const int max_conf;
};

class PCPatternTable : public OffsetPatternTable {
public:
    PCPatternTable(int size, int pattern_len, int tag_size,
                   int num_ways = 16, int max_conf = 32,
                   int debug_level = 0, int cpu = 0) :
        OffsetPatternTable(size, pattern_len, tag_size, num_ways, max_conf, debug_level, cpu) {}

protected:
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
    PrefetchBuffer(int size, int pattern_len, int debug_level = 0, int num_ways = 16) :
        Super(size, num_ways), pattern_len(pattern_len) {
        if (this->debug_level >= 1)
            std::cerr << "PrefetchBuffer::PrefetchBuffer(size=" << size << ", pattern_len=" << pattern_len
                      << ", debug_level=" << debug_level << ", num_ways=" << num_ways << ")" << std::dec << std::endl;
    }

    // int get_size() const {
    //     int count = 0;
    //     for (int i = 0; i < this->size; i++) {
    //         for (int j = 0; j < this->num_ways; j++) {
    //             if (this->data[i][j].valid) {
    //                 count++;
    //             }
    //         }
    //     }
    //     return count;
    // }

    void insert(uint64_t region_number, std::vector<int> pattern) {
        if (this->debug_level >= 2)
            std::cerr << "PrefetchBuffer::insert(region_number=0x" << std::hex << region_number
                      << ", pattern=" << custom_util::pattern_to_string(pattern) << ")" << std::dec << std::endl;
        uint64_t key = this->build_key(region_number);
        Super::insert(key, {pattern});
        Super::rp_insert(key);
    }

    // CLIP integration: expose entry access
    Entry* get_entry_for_region(uint64_t region_number) {
        uint64_t key = this->build_key(region_number);
        return Super::find(key);
    }

       int get_active_entries() const {
        int count = 0;
        // Iterate through all sets and ways
        for (int set = 0; set < this->num_sets; set++) {
            for (int way = 0; way < this->num_ways; way++) {
                if (this->entries[set][way].valid) {
                    count++;
                }
            }
        }
        return count;
    }

    std::string log() {
        std::vector<std::string> headers({"Region", "Pattern"});
        return Super::log(headers);
    }

    int get_index_len() const { return this->index_len; }

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

// ============================================================================
// PMP Main Class with CLIP Integration
// ============================================================================

class PMP {
public:
    PMP(int pattern_len, int offset_width, int opt_size, int opt_max_conf, int opt_ways, int pc_width,
        int ppt_size, int ppt_max_conf, int ppt_ways, int filter_table_size, int ft_way,
        int accumulation_table_size, int at_way, int pf_buffer_size, int pf_buffer_way,
        int FILL_L1, int FILL_L2, int FILL_LLC,
        int debug_level = 0, int cpu = 0) :
        pattern_len(pattern_len),
        opt(opt_size, pattern_len, offset_width, opt_ways, opt_max_conf, debug_level, cpu),
        ppt(ppt_size, pattern_len / PATTERN_DEGRADE_LEVEL, pc_width, ppt_ways, ppt_max_conf, debug_level, cpu),
        filter_table(filter_table_size, debug_level, ft_way),
        accumulation_table(accumulation_table_size, pattern_len, debug_level, at_way),
        pf_buffer(pf_buffer_size, pattern_len, debug_level, pf_buffer_way),
        clip_filter(cpu),
        FILL_L1_PMP(1), FILL_L2_PMP(2), FILL_LLC_PMP(3),
        debug_level(debug_level),
        cpu(cpu) {
        if (this->debug_level >= 1)
            std::cerr << " PMP:: PMP(pattern_len=" << pattern_len
                      << ", filter_table_size=" << filter_table_size
                      << ", accumulation_table_size=" << accumulation_table_size
                      << ", pf_buffer_size=" << pf_buffer_size
                      << ", debug_level=" << debug_level << ")" << std::endl;
    }

    void access(uint64_t block_number, uint64_t pc);
    void eviction(uint64_t block_number);
    int prefetch(CACHE* cache, uint64_t block_number, uint64_t trigger_ip, 
                bool rob_stalled, uint8_t miss_level);
    void set_debug_level(int debug_level);
    void log();

    int get_pattern_buffer_size() const {
        return pf_buffer.get_active_entries();
    }

    // CLIP interface
    clip::CLIPFilter& get_clip_filter() { return clip_filter; }

    int FILL_L1_PMP;
    int FILL_L2_PMP;
    int FILL_LLC_PMP;
    int invalid_by_eviction = 0;
    int invalid_by_max = 0;

     void update_feedback(bool was_useful);

private:
    int max_conf = 32;
    std::vector<int> find_in_opt(uint64_t pc, uint64_t block_number);
    void insert_in_opt(const AccumulationTable::Entry& entry);
    std::vector<int> vote(const std::vector<OffsetPatternTableData>& x, bool is_pc_opt = false);
   
    double get_recent_accuracy() const;

    double adaptive_l1d_thresh = 0.50;
    double adaptive_l2c_thresh = 0.15;
    uint64_t recent_pf_issued = 0;
    uint64_t recent_pf_useful = 0;
    // const double L1D_THRESH = 0.50;
    // const double L2C_THRESH = 0.150;
    const double LLC_THRESH = 1;

    // const double PC_L1D_THRESH = 0.50;
    // const double PC_L2C_THRESH = 0.150;
    const double PC_LLC_THRESH = 1;

    int pattern_len;
    FilterTable filter_table;
    AccumulationTable accumulation_table;
    OffsetPatternTable opt;
    PCPatternTable ppt;
    PrefetchBuffer pf_buffer;
    clip::CLIPFilter clip_filter;  // CLIP integration
    int debug_level = 0;
    int cpu;
};

} // namespace pmp_enhanced

#endif