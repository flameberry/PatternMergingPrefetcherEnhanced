#ifndef SMS_H
#define SMS_H

#include <vector>

#include "custom_util.h"
#include "cache.h"

#define __page_offset(block_num) (block_num & PAGE_OFFSET_MASK)

namespace {
constexpr int NUM_OFFSETS = 1;

constexpr int NUM_BLOCKS = PAGE_SIZE / BLOCK_SIZE;
constexpr uint64_t PAGE_OFFSET_MASK = (1ULL << (LOG2_PAGE_SIZE - LOG2_BLOCK_SIZE)) - 1;

/* SMS settings */
constexpr int REGION_SIZE = 2 * 1024;

constexpr int PT_SIZE = (NUM_OFFSETS == 1 ? 64 : 256);
constexpr int PT_WAY = 1;

constexpr int FT_SIZE = 64;
constexpr int FT_WAY = 8;

constexpr int AT_SIZE = 64;
constexpr int AT_WAY = 8;

constexpr int PB_SIZE = 32;
constexpr int PB_WAY = 8;
} // namespace

namespace sms {

struct FilterTableData {
    uint64_t trigger_offset;
};

class FilterTable : public custom_util::SRRIPSetAssociativeCache<FilterTableData> {
    typedef custom_util::SRRIPSetAssociativeCache<FilterTableData> Super;

public:
    FilterTable(int size, int num_ways) :
        Super(size, num_ways) { assert(__builtin_popcount(size) == 1); }

    Entry* find(uint64_t region_number) {
        uint64_t key = build_key(region_number);
        Entry* entry = Super::find(key);
        if (!entry)
            return nullptr;
        Super::rp_promote(key);
        return entry;
    }

    void insert(uint64_t page_num, uint64_t trigger_offset) {
        uint64_t key = build_key(page_num);
        auto entry = Super::insert(key, {trigger_offset});
        Super::rp_insert(key);
    }

    Entry* erase(uint64_t page_num) {
        uint64_t key = build_key(page_num);
        return Super::erase(key);
    }

    std::string log() {
        std::vector<std::string> headers({"PageNum", "Trigger"});
        return Super::log(headers);
    }

private:
    uint64_t build_key(uint64_t page_num) {
        uint64_t key = page_num & ((1ULL << 37) - 1);
        return custom_util::hash_index(key, this->index_len);
    }
    void write_data(Entry& entry, custom_util::Table& table, int row) {
        uint64_t key = custom_util::hash_index(entry.key, this->index_len);
        table.set_cell(row, 0, key);
        table.set_cell(row, 1, entry.data.trigger_offset);
    }
};

struct AccumulationTableData {
    std::vector<uint64_t> first_offsets;
    std::vector<bool> pattern;
    int num_different_offsets;
};

class AccumulationTable : public custom_util::LRUSetAssociativeCache<AccumulationTableData> {
    typedef custom_util::LRUSetAssociativeCache<AccumulationTableData> Super;

public:
    AccumulationTable(int size, int num_ways) :
        Super(size, num_ways) {
    }

    Entry* set_pattern(uint64_t page_num, uint64_t offset) {
        uint64_t key = build_key(page_num);
        Entry* entry = Super::find(key);
        if (!entry)
            return nullptr;
        else {
            if (!entry->data.pattern[offset]) {
                entry->data.pattern[offset] = true;
                if (entry->data.num_different_offsets < NUM_OFFSETS) {
                    entry->data.first_offsets.push_back(offset);
                    entry->data.num_different_offsets++;
                }
            }
            Super::rp_promote(key);
            return entry;
        }
    }

    Entry insert(uint64_t page_num, uint64_t trigger_offset, uint64_t second_offset) {
        uint64_t key = build_key(page_num);
        std::vector<bool> pattern(NUM_BLOCKS, false);
        std::vector<uint64_t> first_offsets;

        pattern[trigger_offset] = pattern[second_offset] = true;
        first_offsets.push_back(trigger_offset);
        if (NUM_OFFSETS > 1)
            first_offsets.push_back(second_offset);

        Entry old_entry = Super::insert(key, {first_offsets, pattern, first_offsets.size()});
        Super::rp_insert(key);
        return old_entry;
    }

    Entry* erase(uint64_t page_num) {
        uint64_t key = build_key(page_num);
        return Super::erase(key);
    }

    std::string log() {
        std::vector<std::string> headers;
        headers.push_back("PageNum");
        for (int i = 0; i < NUM_OFFSETS; i++) {
            headers.push_back(std::to_string(i + 1));
        }
        headers.push_back("Pattern");
        return Super::log(headers);
    }

    std::vector<int> get_num_triggers() {
        std::vector<int> num_triggers(NUM_BLOCKS, 0);
        auto valid_entries = Super::get_valid_entries();
        for (auto entry : valid_entries) {
            num_triggers[entry.data.first_offsets[0]]++;
        }
        return num_triggers;
    }

private:
    void write_data(Entry& entry, custom_util::Table& table, int row) {
        uint64_t key = custom_util::hash_index(entry.key, this->index_len);

        table.set_cell(row, 0, key);
        for (int i = NUM_OFFSETS; i > 0; i--) {
            table.set_cell(row, NUM_OFFSETS - i + 1, int(entry.data.first_offsets[NUM_OFFSETS - i]));
        }
        table.set_cell(row, NUM_OFFSETS + 1, custom_util::pattern_to_string(entry.data.pattern));
    }

    uint64_t build_key(uint64_t page_num) {
        uint64_t key = page_num & ((1ULL << 37) - 1);
        return custom_util::hash_index(key, this->index_len);
    }
};

class PatternHistoryTableData {
public:
    std::vector<bool> pattern;
};

class PatternHistoryTable : custom_util::LRUSetAssociativeCache<PatternHistoryTableData> {
    typedef custom_util::LRUSetAssociativeCache<PatternHistoryTableData> Super;

public:
    PatternHistoryTable(
        int size, int num_ways) :
        Super(size, num_ways) {
    }

    /* address is actually block number */
    void insert(std::vector<uint64_t> first_offsets, std::vector<bool> pattern) {
        assert(first_offsets.size() == NUM_OFFSETS);
        uint64_t key = build_key(first_offsets);
        Entry* entry = Super::find(key);

        if (entry) {
            auto& stored_pattern = entry->data.pattern;

            for (int i = 0; i < NUM_BLOCKS; i++) {
                if (pattern[i]) {
                    stored_pattern[i] = true;
                } else
                    stored_pattern[i] = false;
            }
            Super::rp_promote(key);

        } else {
            Super::insert(key, {pattern});
            Super::rp_insert(key);
        }
    }

    Entry* find(std::vector<uint64_t> first_offsets) {
        assert(first_offsets.size() == NUM_OFFSETS);
        uint64_t key = build_key(first_offsets);
        return Super::find(key);
    }

    std::string log() {
        std::vector<std::string> headers;
        for (int i = 0; i < NUM_OFFSETS; i++) {
            headers.push_back(std::to_string(i + 1));
        }
        headers.push_back("Pattern");
        return Super::log(headers);
    }

private:
    void write_data(Entry& entry, custom_util::Table& table, int row) {
        int shift = 0;
        uint64_t mask = BLOCK_SIZE - 1, head = 0;
        for (int i = NUM_OFFSETS; i > 0; i--) {
            head = (entry.key >> shift) & mask;
            shift += LOG2_BLOCK_SIZE;
            table.set_cell(row, NUM_OFFSETS - i, int(head));
        }
        table.set_cell(row, NUM_OFFSETS, custom_util::pattern_to_string(entry.data.pattern));
    }

    uint64_t build_key(std::vector<uint64_t> first_offsets) {
        assert(first_offsets.size() <= 8);
        uint64_t key = 0;
        int shift = 0;
        for (auto offset : first_offsets) {
            key |= (offset << shift);
            shift += LOG2_BLOCK_SIZE;
        }
        return key;
    }
};

struct PrefetchBufferData {
    std::vector<bool> pattern;
    std::vector<uint64_t> first_offsets;
    uint32_t pf_metadata;
};

class PrefetchBuffer : public custom_util::LRUSetAssociativeCache<PrefetchBufferData> {
    typedef custom_util::LRUSetAssociativeCache<PrefetchBufferData> Super;

public:
    PrefetchBuffer(int size, int pattern_len, int debug_level = 0, int num_ways = 8) :
        Super(size, num_ways), pattern_len(pattern_len) {
    }

    void insert(uint64_t page_num, std::vector<bool> pattern, std::vector<uint64_t> first_offsets, uint32_t pf_metadata) {
        uint64_t key = this->build_key(page_num);
        Super::insert(key, {pattern, first_offsets, pf_metadata});
        Super::rp_insert(key);
    }

    void prefetch(CACHE* cache, uint64_t block_num) {
        uint64_t page_offset = __page_offset(block_num);
        uint64_t page_num = block_num >> (LOG2_PAGE_SIZE - LOG2_BLOCK_SIZE);
        // std::cout << "prefetch: " << page_num << std::endl;
        uint64_t key = this->build_key(page_num);
        auto entry = Super::find(key);
        if (!entry) {
            return;
        }
        // std::cout << "Prefetch found" << std::endl;
        Super::rp_promote(key);
        std::vector<bool>& pattern = entry->data.pattern;
        uint32_t pf_metadata = entry->data.pf_metadata;
        auto first_offsets = entry->data.first_offsets;

        pattern[page_offset] = false;
        for (uint64_t i = 1; i < BLOCK_SIZE; i++) {
            uint64_t pf_offset = ((uint64_t)page_offset + i) % BLOCK_SIZE;
            bool fetched = false;
            for (auto offset : first_offsets) {
                if (offset == pf_offset) {
                    fetched = true;
                }
            }

            if (pattern[pf_offset] && !fetched) {
                uint64_t pf_addr = (page_num << LOG2_PAGE_SIZE) + (pf_offset << LOG2_BLOCK_SIZE);
                if (cache->get_occupancy(3, 0) + cache->get_occupancy(0, 0) < cache->get_size(0, 0) - 1 && cache->get_occupancy(3, 0) < cache->get_size(3, 0)) {
                    int ok = cache->prefetch_line(pf_addr, true, pf_metadata);
                    pattern[pf_offset] = false;
                } else {
                    return;
                }
            }
        }
        Super::erase(key);
        return;
    }
    std::string log() {
        std::vector<std::string> headers;
        headers.push_back("PageNum");
        for (int i = 0; i < NUM_OFFSETS; i++) {
            headers.push_back(std::to_string(i + 1));
        }
        headers.push_back("Meta");
        headers.push_back("Pattern");
        return Super::log(headers);
    }

private:
    void write_data(Entry& entry, custom_util::Table& table, int row) {
        uint64_t key = custom_util::hash_index(entry.key, this->index_len);

        table.set_cell(row, 0, key);
        for (int i = NUM_OFFSETS; i > 0; i--) {
            table.set_cell(row, NUM_OFFSETS - i + 1, int(entry.data.first_offsets[NUM_OFFSETS - i]));
        }
        table.set_cell(row, NUM_OFFSETS + 1, (uint64_t)entry.data.pf_metadata);
        table.set_cell(row, NUM_OFFSETS + 2, custom_util::pattern_to_string(entry.data.pattern));
    }

    uint64_t build_key(uint64_t page_num) {
        uint64_t key = page_num;
        return key;
    }

    int pattern_len;
};

class SMS_MultiOffsets {
public:
    SMS_MultiOffsets(int ft_size, int ft_ways, int at_size, int at_ways, int pt_size, int pt_ways, int pb_size, int pb_ways, int cpu = 0) :
        ft(ft_size, ft_ways), at(at_size, at_ways), pt(pt_size, pt_ways), pb(pb_size, pb_ways), cpu(cpu) {
    }
    int global_level = 0;
    bool warmup;
    SMS_MultiOffsets();

    void access(uint64_t block_num, uint64_t ip, CACHE* cache);
    void eviction(uint64_t block_num);
    void prefetch(CACHE* cache, uint64_t block_num);

    void log();

    void pattern_prefetch(uint64_t trigger, uint64_t second);

private:
    std::vector<bool> find_in_pt(std::vector<uint64_t> first_offsets) {
        std::vector<bool> ret(NUM_BLOCKS, false);

        auto entry = pt.find(first_offsets);
        if (!entry) {
            __second_missed++;
            return ret;
        } else
            return entry->data.pattern;
    }

    void insert_in_pt(const AccumulationTable::Entry& entry) {
        if (entry.data.first_offsets.size() == NUM_OFFSETS) {
            pt.insert(entry.data.first_offsets, entry.data.pattern);
            if (recorded_patterns.size() < 100000 && !warmup)
                recorded_patterns.push_back(entry);
        }
    }

    int __second_missed = 0;

    std::vector<AccumulationTable::Entry> recorded_patterns;

    FilterTable ft;
    AccumulationTable at;
    PatternHistoryTable pt;
    PrefetchBuffer pb;
    int cpu;
};
} // namespace sms

#endif