#ifndef GAZE_H
#define GAZE_H

#include "custom_util.h"
#include "cache.h"

#include <stdint.h>
#include <random>
#include <deque>

std::map<uint64_t, std::vector<int>> region_map_load, region_map_pref;
namespace gaze {

#define __region_offset(block_num) (block_num & REGION_OFFSET_MASK)
#define FT_TYPE custom_util::SRRIPSetAssociativeCache
#define AT_TYPE custom_util::LRUSetAssociativeCache
#define PT_TYPE custom_util::LRUSetAssociativeCache
#define PB_TYPE custom_util::LRUSetAssociativeCache

constexpr uint64_t REGION_SIZE = 4 * 1024; // '4KB', '8KB', '32KB', '128KB', '512KB', '1024KB', '2048KB'
constexpr uint64_t LOG2_REGION_SIZE = champsim::lg2(REGION_SIZE);
constexpr uint64_t REGION_OFFSET_MASK = (1ULL << (LOG2_REGION_SIZE - LOG2_BLOCK_SIZE)) - 1;

constexpr int NUM_BLOCKS = REGION_SIZE / BLOCK_SIZE;
constexpr int STRIDE_PF_LOOKAHEAD = 2;
constexpr int MAX_CONF = 16;
constexpr float PF_THRESH_L2 = 0.15;
constexpr float PF_THRESH_L1 = 0.5;
constexpr int PF_FILL_L1 = 1;
constexpr int PF_FILL_L2 = 2;

std::pair<float, float> calculate_acc_and_cov(std::vector<int> pattern_1, std::vector<int> pattern_2);
bool different_patterns(std::vector<int> pattern_1, std::vector<int> pattern_2);
std::vector<int> pattern_bool2int(std::vector<bool> pattern);
bool pattern_all_set(std::vector<bool> pattern);
bool pattern_all_set(std::vector<int> pattern);
// std::vector<bool> pattern_int2bool(std::vector<int> pattern);

struct FilterTableData {
    uint64_t trigger_offset;
    uint64_t pc;
};

// Filter Table
class FilterTable : public FT_TYPE<FilterTableData> {
    typedef FT_TYPE<FilterTableData> Super;

public:
    FilterTable(int size, int num_ways) :
        Super(size, num_ways) {
    }

    Entry* find(uint64_t region_num) {
        uint64_t key = build_key(region_num);
        Entry* entry = Super::find(key);
        if (!entry) {
            return nullptr;
        } else {
            Super::rp_promote(key);
            return entry;
        }
    }

    void insert(uint64_t region_num, uint64_t trigger_offset, uint64_t pc) {
        uint64_t key = build_key(region_num);
        auto entry = Super::insert(key, {trigger_offset, pc});
        if (entry.valid)
            this->__ft_invalid_entry_eviction++;
        Super::rp_insert(key);
        this->__insertion++;
    }

    Entry* erase(uint64_t region_num) {
        uint64_t key = build_key(region_num);
        return Super::erase(key);
    }

    std::string log() {
        std::vector<std::string> headers({"RegionNum", "Trigger", "PC"});
        return Super::log(headers);
    }

private:
    uint64_t build_key(uint64_t region_num) {
        uint64_t key = region_num & ((1ULL << 37) - 1);
        return custom_util::hash_index(key, this->index_len);
    }

    void write_data(Entry& entry, custom_util::Table& table, int row) {
        uint64_t key = custom_util::hash_index(entry.key, this->index_len);
        table.set_cell(row, 0, key);
        table.set_cell(row, 1, entry.data.trigger_offset);
        table.set_cell(row, 2, entry.data.pc);
    }

    int __ft_invalid_entry_eviction = 0;
    int __ft_valid_entry_eviction = 0;
    int __insertion = 0;

public:
    auto get_ft_invalid_entry_eviction() {
        return __ft_invalid_entry_eviction;
    }

    auto get_ft_valid_entry_eviction() {
        return __ft_valid_entry_eviction;
    }

    auto get_insertion() {
        return __insertion;
    }

    void increase_ft_invalid_entry_eviction() {
        __ft_invalid_entry_eviction++;
    }

    void increase_ft_valid_entry_eviction() {
        __ft_valid_entry_eviction++;
    }
};

struct AccumulateTableData {
    uint64_t trigger_offset;
    uint64_t second_offset;
    uint64_t pc;
    bool missed_in_pt;
    std::vector<bool> pattern;
    std::vector<int> order;

    int last_stride;
    uint64_t last_offset;

    bool con = false;

    int timestamp = 2;
};

class AccumulateTable : public AT_TYPE<AccumulateTableData> {
    typedef AT_TYPE<AccumulateTableData> Super;

public:
    AccumulateTable(int size, int num_ways) :
        Super(size, num_ways) {
    }

    Entry* set_pattern(uint64_t region_num, uint64_t offset) {
        uint64_t key = build_key(region_num);
        Entry* entry = Super::find(key);
        if (!entry)
            return nullptr;
        else {
            if (!entry->data.pattern[offset]) {
                entry->data.timestamp++;
                int stride = int(offset) - int(entry->data.last_offset);
                // stride if off
                // if (entry->data.missed_in_pt || entry->data.con)
                //     this->__stride_prefetch = (stride == entry->data.last_stride);
                entry->data.order[offset] = entry->data.timestamp;
                entry->data.pattern[offset] = true;
                entry->data.last_offset = offset;
                entry->data.last_stride = stride;
            }
            Super::rp_promote(key);
            return entry;
        }
    }

    Entry insert(uint64_t region_num, uint64_t trigger_offset, uint64_t second_offset, uint64_t pc, bool missed_in_pt, bool con) {
        // if (missed_in_pt)
        //     std::cout << "missed in pt" << std::endl;
        uint64_t key = build_key(region_num);
        std::vector<bool> pattern(NUM_BLOCKS, false);
        std::vector<int> order(NUM_BLOCKS, 0);
        pattern[trigger_offset] = pattern[second_offset] = true;
        order[trigger_offset] = 1;
        order[second_offset] = 2;
        int last_stride = int(second_offset) - int(trigger_offset);
        Entry old_entry = Super::insert(key, {trigger_offset, second_offset, pc, missed_in_pt, pattern, order, last_stride, second_offset, con});
        Super::rp_insert(key);
        return old_entry;
    }

    Entry* erase(uint64_t region_num) {
        uint64_t key = build_key(region_num);
        return Super::erase(key);
    }

    std::string log() {
        std::vector<std::string> headers({"RegionNum", "Trigger", "Second", "PC", "Pattern", "Order"});
        return Super::log(headers);
    }

    std::vector<int> get_num_triggers() {
        std::vector<int> num_triggers(NUM_BLOCKS, 0);
        auto valid_entries = Super::get_valid_entries();
        for (auto entry : valid_entries) {
            num_triggers[entry.data.trigger_offset]++;
        }
        return num_triggers;
    }

private:
    void write_data(Entry& entry, custom_util::Table& table, int row) {
        uint64_t key = custom_util::hash_index(entry.key, this->index_len);
        table.set_cell(row, 0, key);
        table.set_cell(row, 1, entry.data.trigger_offset);
        table.set_cell(row, 2, entry.data.second_offset);
        table.set_cell(row, 3, entry.data.pc);
        table.set_cell(row, 4, custom_util::pattern_to_string(entry.data.pattern));
        table.set_cell(row, 5, custom_util::pattern_to_string(entry.data.order));
    }

    uint64_t build_key(uint64_t region_num) {
        uint64_t key = region_num & ((1ULL << 37) - 1);
        return custom_util::hash_index(key, this->index_len);
    }

    bool __stride_prefetch = false;

public:
    bool get_stride_prefetch() {
        return __stride_prefetch;
    }

    void turn_off_stride_prefetch() {
        __stride_prefetch = false;
    }
};

struct PatternTableData {
    std::vector<int> pattern;
    uint64_t pc;
    bool con = false;

    PatternTableData() {
        pattern = std::vector<int>(NUM_BLOCKS, 0);
        pc = 0;
    }
    PatternTableData(std::vector<int> pattern, uint64_t pc) :
        pattern(pattern), pc(pc) {}
    PatternTableData(std::vector<int> pattern, uint64_t pc, bool con) :
        pattern(pattern), pc(pc), con(con) {}
};

class PatternTable : public PT_TYPE<PatternTableData> {
    typedef PT_TYPE<PatternTableData> Super;

public:
    PatternTable(int size, int num_ways) :
        Super(size, num_ways) {
        // assert(size == NUM_BLOCKS * num_ways);
        std::cout << "Pattern Table index_len: " << Super::index_len << std::endl;
    }

    void insert(uint64_t trigger, uint64_t second, uint64_t pc, uint64_t region_num, std::vector<bool> pattern) {
        // if (region_num == 5152 || region_num == 18179) {
        //     std::cout << "AT Pattern: " << region_num << std::endl;
        //     for (auto p : pattern) {
        //         std::cout << p << " ";
        //     }
        //     std::cout << std::endl;
        // }
        assert(pattern[trigger] && pattern[second]);
        bool all_set = pattern_all_set(pattern);

        if (trigger != 0 || second != 1) { // not special
            uint64_t key = build_key(trigger, second, pc, region_num);
            Super::insert(key, {pattern_bool2int(pattern), pc});
            Super::rp_insert(key);
        } else { // special
            if (all_set) {
                if (con_counter < 8)
                    con_counter++;
                uint64_t hashed_pc = custom_util::my_hash_index(pc, LOG2_BLOCK_SIZE, 8);
                if (con_pc.end() == std::find_if(con_pc.begin(), con_pc.end(), [hashed_pc](auto& x) { return x == hashed_pc; })) {
                    if (con_pc.size() == 8)
                        con_pc.pop_back();
                    con_pc.push_front(hashed_pc);
                }
            } else {
                if (con_counter > 2)
                    con_counter >> 1;
                else if (con_counter > 0)
                    con_counter--;
            }
        }
    }

    Entry* find(uint64_t trigger, uint64_t second, uint64_t pc, uint64_t region_num) {
        if (trigger != 0 || second != 1) { // not special
            uint64_t key = build_key(trigger, second, pc, region_num);
            // return Super::find(key);
            // pht is off
            return nullptr;
        } else {
            uint64_t hashed_pc = custom_util::my_hash_index(pc, LOG2_BLOCK_SIZE, 8);

            if (con_counter == 8 || con_pc.end() != std::find_if(con_pc.begin(), con_pc.end(), [hashed_pc](auto& x) { return x == hashed_pc; })) {
                Entry* ret = new Entry();
                ret->data.con = true;
                for (int i = 0; i < NUM_BLOCKS / 4; i++) {
                    ret->data.pattern[i] = PF_FILL_L1;
                }
                for (int i = NUM_BLOCKS / 4; i < NUM_BLOCKS; i++) {
                    ret->data.pattern[i] = PF_FILL_L1;
                }
                return ret;
            } else if (con_counter > 2) {
                Entry* ret = new Entry();
                ret->data.con = true;
                for (int i = 0; i < NUM_BLOCKS / 4; i++) {
                    ret->data.pattern[i] = PF_FILL_L1;
                }
                return ret;
            }
            return nullptr;
        }
        assert(0);
    }

    std::string log() {
        std::vector<std::string> headers({"Trigger", "Second", "Pattern"});
        return Super::log(headers);
    }

    std::deque<uint64_t> con_pc;
    int con_counter = 0;

private:
    void write_data(Entry& entry, custom_util::Table& table, int row) {
        table.set_cell(row, 0, int(entry.key & uint64_t((1ULL << this->index_len) - 1)));
        table.set_cell(row, 1, int((entry.key >> this->index_len) & ((1ULL << this->index_len) - 1)));
        table.set_cell(row, 2, custom_util::pattern_to_string(entry.data.pattern));
    }

    uint64_t build_key(uint64_t trigger, uint64_t second, uint64_t pc, uint64_t region_num) {
        assert(trigger >= 0 && trigger < NUM_BLOCKS && second >= 0 && second < NUM_BLOCKS);
        uint64_t key = (second << this->index_len) | trigger;
        return key;
    }
};

struct PrefetchBufferData {
public:
    std::vector<int> pattern;
    uint64_t trigger;
    uint64_t second;
    std::vector<int> pf_metadata;
};

class PrefetchBuffer : public PB_TYPE<PrefetchBufferData> {
    typedef PB_TYPE<PrefetchBufferData> Super;

public:
    PrefetchBuffer(int size, int pattern_len, int debug_level = 0, int num_ways = 16) :
        Super(size, num_ways), pattern_len(pattern_len) {
    }

    void insert(uint64_t region_num, std::vector<int> pattern, uint64_t trigger, uint64_t second, uint32_t pf_metadata) {
        // std::cout << "insert: " << region_num << std::endl;
        // if (!warmup && (region_num == 5152 || region_num == 18179)) {
        //     std::cout << "Prefetch Pattern: " << region_num << std::endl;
        //     for (auto p : pattern) {
        //         std::cout << p << " ";
        //     }
        //     std::cout << std::endl;
        // }
        uint64_t key = this->build_key(region_num);
        if ((pf_metadata & 3) == 0 || (pf_metadata & 3) == 3) { // stride & promote
            if ((pf_metadata & 3) == 0)
                num_stride_issued_regions++;
            auto entry = find(key);
            if (!entry) {
                Super::insert(key, {pattern, trigger, trigger, std::vector<int>(gaze::NUM_BLOCKS, pf_metadata)});
                Super::rp_insert(key);
            } else {
                for (int i = 0; i < NUM_BLOCKS; i++) {
                    if (pattern[i] == PF_FILL_L1) {
                        if (entry->data.pattern[i] != PF_FILL_L1) {
                            if (entry->data.pf_metadata[i] == 2) { // from con, promote
                                entry->data.pf_metadata[i] = 3;    // set to promoted
                            }
                        }
                        entry->data.pattern[i] = PF_FILL_L1;
                    }
                }
                Super::rp_promote(key);
            }
        } else { // con and dis
            if ((pf_metadata & 3) == 1)
                num_dis_issued_regions++;
            else
                num_con_issued_regions++;
            Super::insert(key, {pattern, trigger, second, std::vector<int>(gaze::NUM_BLOCKS, pf_metadata)});
            Super::rp_insert(key);
        }
    }

    void prefetch(CACHE* cache, uint64_t block_num) {
        uint64_t region_offset = __region_offset(block_num);
        uint64_t region_num = block_num >> (LOG2_REGION_SIZE - LOG2_BLOCK_SIZE);
        // std::cout << "prefetch: " << region_num << std::endl;
        uint64_t key = this->build_key(region_num);
        auto entry = Super::find(key);
        if (!entry) {
            return;
        }
        // std::cout << "Prefetch found" << std::endl;
        Super::rp_promote(key);
        std::vector<int>& pattern = entry->data.pattern;
        auto pf_metadatas = entry->data.pf_metadata;
        uint32_t pf_metadata = 0;
        uint64_t trigger = entry->data.trigger;
        uint64_t second = entry->data.second;

        pattern[region_offset] = 0;
        for (uint64_t i = 1; i < (REGION_SIZE / BLOCK_SIZE); i++) {
            uint64_t pf_offset = ((uint64_t)region_offset + i) % (REGION_SIZE / BLOCK_SIZE);
            if (pf_offset != trigger && pf_offset != second && pattern[pf_offset] != 0) {
                uint64_t pf_addr = (region_num << LOG2_REGION_SIZE) + (pf_offset << LOG2_BLOCK_SIZE);
                // std::cout << "pf_addr " << pf_addr << std::endl;
                if (cache->get_occupancy(3, 0) + cache->get_occupancy(0, 0) < cache->get_size(0, 0) - 1 && cache->get_occupancy(3, 0) < cache->get_size(3, 0)) {
                    pf_metadata = pf_metadatas[pf_offset];
                    pf_metadata = __add_pf_sour_level(pf_metadata, 1);
                    if (pattern[pf_offset] == PF_FILL_L1) {
                        pf_metadata = __add_pf_dest_level(pf_metadata, 1);
                    } else {
                        pf_metadata = __add_pf_dest_level(pf_metadata, 2);
                    }
                    int ok = cache->prefetch_line(pf_addr, pattern[pf_offset] == PF_FILL_L1 ? true : false, pf_metadata);

                    // int ok = cache->prefetch_line(pf_addr, true, pf_metadata);
                    __pf_issued += ok;
                    if (ok) {
                        if (!warmup) {
                            if (region_map_pref.find(region_num) == region_map_pref.end()) {
                                region_map_pref.insert({region_num, std::vector<int>(gaze::NUM_BLOCKS, 0)});
                            }
                            region_map_pref.at(region_num)[pf_offset] = 1; // prefetch

                            if ((pf_metadata & 3) == 0) {
                                __stride_issued += ok;
                                num_stride_issued += ok;
                            } else {
                                __pattern_issued += ok;
                                if ((pf_metadata & 3) == 2) {
                                    __pattern_con_issued += ok;
                                    num_con_issued += ok;
                                } else if ((pf_metadata & 3) == 1) {
                                    num_dis_issued += ok;
                                } else {
                                    assert((pf_metadata & 3) == 3);
                                    num_con_issued += ok;
                                    num_stride_promote += ok;
                                }
                            }
                            if (pattern[pf_offset] == PF_FILL_L1) {
                                prefetch_to_l1++;
                            } else {
                                prefetch_to_l2++;
                            }
                        }
                        pattern[pf_offset] = 0;
                    }
                } else {
                    return;
                }
            }
        }
        Super::erase(key);
        return;
    }

    std::string log() {
        std::vector<std::string> headers({"RegionNum", "Trigger", "Second", "Meta", "Pattern"});
        return Super::log(headers);
    }

private:
    void write_data(Entry& entry, custom_util::Table& table, int row) {
        uint64_t key = custom_util::hash_index(entry.key, this->index_len);
        table.set_cell(row, 0, key);
        table.set_cell(row, 1, entry.data.trigger);
        table.set_cell(row, 2, entry.data.second);
        table.set_cell(row, 3, (uint64_t)entry.data.pf_metadata[0]);
        table.set_cell(row, 4, custom_util::pattern_to_string(entry.data.pattern));
    }

    uint64_t build_key(uint64_t region_num) {
        uint64_t key = region_num;
        return key;
    }

    int pattern_len;
    int __pf_issued = 0;
    int __stride_issued = 0;
    int __pattern_issued = 0;
    int __pattern_con_issued = 0;

public:
    bool warmup;
    int prefetch_to_l2 = 0, prefetch_to_l1 = 0;
    int num_con_issued = 0, num_stride_issued = 0, num_stride_promote = 0, num_dis_issued = 0;
    int num_stride_issued_regions = 0, num_dis_issued_regions = 0, num_con_issued_regions = 0;
    int get_pf_issued() {
        return __pf_issued;
    }

    int get_stride_issued() {
        return __stride_issued;
    }

    int get_pattern_issued() {
        return __pattern_issued;
    }

    int get_pattern_con_issued() {
        return __pattern_con_issued;
    }
};

class Gaze {
public:
    Gaze(int ft_size, int ft_ways, int at_size, int at_ways, int pt_size, int pt_ways, int pb_size, int pb_ways, int cpu = 0) :
        ft(ft_size, ft_ways), at(at_size, at_ways), pt(pt_size, pt_ways), pb(pb_size, pb_ways), cpu(cpu) {
    }
    int global_level = 0;
    bool warmup;
    Gaze();

    void access(uint64_t block_num, uint64_t ip, CACHE* cache);
    void eviction(uint64_t block_num);
    void prefetch(CACHE* cache, uint64_t block_num);

    void log();

    void stride_prefetch(uint64_t block_num);
    void pattern_prefetch(uint64_t trigger, uint64_t second);

    void tune_stride_degree(CACHE* cache);

    int continue_pattern_per_block_counter[gaze::NUM_BLOCKS] = {0};
    int continue_pattern_per_block_counter_01[gaze::NUM_BLOCKS] = {0};

private:
    PatternTable::Entry* find_in_pt(uint64_t trigger, uint64_t second, uint64_t pc, uint64_t region_num) {
        auto entry = pt.find(trigger, second, pc, region_num);
        if (!entry) {
            __pt_missed++;
            return entry;
        } else
            return entry;
    }

    void insert_in_pt(const AccumulateTable::Entry& entry, uint64_t region_num) {
        uint64_t trigger = entry.data.trigger_offset, second = entry.data.second_offset, pc = entry.data.pc;
        pt.insert(trigger, second, pc, region_num, entry.data.pattern);
    }

    int dissimilarity_counter[NUM_BLOCKS] = {0};
    int stride_pf_degree = 4;
    int stride_pf_inacc_counter = 0;
    bool stride_pf_off = false;
    int stride_off_saturator = 0;
    const int stride_off_saturate_bound = 8;

    int __pt_missed = 0;
    int __pt_missed_second = 0;
    int __pt_missed_pc = 0;
    int __pt_missed_pc_issued_by_counter = 0;

    FilterTable ft;
    AccumulateTable at;
    PatternTable pt;
    PrefetchBuffer pb;
    int cpu;

public:
    void set_warmup(bool warmup) {
        this->warmup = warmup;
        this->pb.warmup = warmup;
    }

    auto get_ft() {
        return ft;
    }

    auto get_at() {
        return at;
    }

    auto get_pt() {
        return pt;
    }

    auto get_pb() {
        return pb;
    }

    auto get_pt_missed() {
        return __pt_missed;
    }
    auto get_pt_missed_second() {
        return __pt_missed_second;
    }
    auto get_pt_missed_pc() {
        return __pt_missed_pc;
    }
    auto get_pt_missed_pc_issued_by_counter() {
        return __pt_missed_pc_issued_by_counter;
    }
};

} // namespace gaze

#endif