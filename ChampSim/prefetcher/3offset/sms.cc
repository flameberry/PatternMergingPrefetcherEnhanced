/* SMS [https://parsa.epfl.ch/stems/papers/isca06.pdf] */
/* PC+Offset */

#include "cache.h"
#include <bits/stdc++.h>
#include "custom_util.h"
#include "sms.h"

using namespace std;

namespace {
std::vector<sms::SMS_MultiOffsets> prefetchers;
} // namespace
namespace sms {

void SMS_MultiOffsets::access(uint64_t block_num, uint64_t ip, CACHE* cache) {
    uint64_t page_num = block_num >> (LOG2_PAGE_SIZE - LOG2_BLOCK_SIZE);
    uint64_t page_offset = __page_offset(block_num);
    auto at_entry = this->at.set_pattern(page_num, page_offset);
    if (NUM_OFFSETS == 1) {
        if (at_entry) {
            return;
        } else {
            auto entry = ft.find(page_num);
            if (!entry) {
                ft.insert(page_num, page_offset);
                std::vector<uint64_t> first_offset{page_offset};
                auto pattern = find_in_pt(first_offset);
                bool pattern_empty = (pattern.end() == std::find_if(pattern.begin(), pattern.end(), [](auto x) { return x == true; }));
                if (!pattern_empty)
                    pb.insert(page_num, pattern, first_offset, 1);
                return;
            } else if (entry->data.trigger_offset != page_offset) { // SECOND OFFSET
                auto at_victim = at.insert(page_num, entry->data.trigger_offset, page_offset);
                ft.erase(page_num);
                if (at_victim.valid) {
                    insert_in_pt(at_victim);
                }
            }
        }
    } else if (NUM_OFFSETS == 2) {
        if (at_entry) {
            return;
        } else {
            auto entry = ft.find(page_num);
            if (!entry) {
                ft.insert(page_num, page_offset);
                return;
            } else if (entry->data.trigger_offset != page_offset) { // SECOND OFFSET
                std::vector<uint64_t> first_2_offsets{entry->data.trigger_offset, page_offset};
                auto pattern = find_in_pt(first_2_offsets);
                bool pattern_empty = (pattern.end() == std::find_if(pattern.begin(), pattern.end(), [](auto x) { return x == true; }));
                if (!pattern_empty)
                    pb.insert(page_num, pattern, first_2_offsets, 1);

                auto at_victim = at.insert(page_num, entry->data.trigger_offset, page_offset);
                ft.erase(page_num);
                if (at_victim.valid) {
                    insert_in_pt(at_victim);
                }
            }
        }
    } else { // 3 or 4
        if (at_entry) {
            if (at_entry->data.num_different_offsets == NUM_OFFSETS) {
                auto first_offsets = at_entry->data.first_offsets;
                assert(first_offsets.size() == NUM_OFFSETS);
                auto pattern = find_in_pt(first_offsets);
                bool pattern_empty = (pattern.end() == std::find_if(pattern.begin(), pattern.end(), [](auto x) { return x == true; }));
                if (!pattern_empty)
                    pb.insert(page_num, pattern, first_offsets, 1);
            }
            return;
        } else {
            auto entry = ft.find(page_num);
            if (!entry) {
                ft.insert(page_num, page_offset);
                return;
            } else if (entry->data.trigger_offset != page_offset) {
                auto at_victim = at.insert(page_num, entry->data.trigger_offset, page_offset);
                ft.erase(page_num);
                if (at_victim.valid) {
                    insert_in_pt(at_victim);
                }
            }
        }
    }
}

void SMS_MultiOffsets::eviction(uint64_t block_num) {
    uint64_t page_num = block_num >> (LOG2_PAGE_SIZE - LOG2_BLOCK_SIZE);
    ft.erase(page_num);
    auto entry = at.erase(page_num);
    if (entry) {
        insert_in_pt(*entry);
    }
}

void SMS_MultiOffsets::prefetch(CACHE* cache, uint64_t block_num) {
    pb.prefetch(cache, block_num);
}

void SMS_MultiOffsets::log() {
    std::cerr << "Filter table begin" << std::dec << std::endl;
    std::cerr << this->ft.log();
    std::cerr << "Filter table end" << std::endl;

    std::cerr << "Accumulation table begin" << std::dec << std::endl;
    std::cerr << this->at.log();
    std::cerr << "Accumulation table end" << std::endl;

    std::cerr << "DissimPattern table begin" << std::dec << std::endl;
    std::cerr << this->pt.log();
    std::cerr << "DissimPattern table end" << std::endl;

    std::cerr << "Prefetch buffer begin" << std::dec << std::endl;
    std::cerr << this->pb.log();
    std::cerr << "Prefetch buffer end" << std::endl;
}
} // namespace sms
void CACHE::prefetcher_initialize() {
    std::cout << NAME << " SMS_" << NUM_OFFSETS << "_Offsets prefetcher" << std::endl;

    prefetchers = std::vector<sms::SMS_MultiOffsets>(
        NUM_CPUS, sms::SMS_MultiOffsets(FT_SIZE, FT_WAY, AT_SIZE, AT_WAY, PT_SIZE, PT_WAY, PB_SIZE, PB_WAY, cpu));
}

uint32_t CACHE::prefetcher_cache_operate(uint64_t addr, uint64_t ip, uint8_t cache_hit, uint8_t type, uint32_t metadata_in) {
    /* call prefetcher and send prefetches */
    prefetchers[cpu].warmup = warmup;
    if (type != LOAD)
        return metadata_in;
    uint64_t block_num = addr >> LOG2_BLOCK_SIZE;

    prefetchers[cpu].access(block_num, ip, this);

    prefetchers[cpu].prefetch(this, block_num);

    return metadata_in;
}

uint32_t CACHE::prefetcher_cache_fill(uint64_t addr, uint32_t set, uint32_t way, uint8_t prefetch, uint64_t evicted_addr, uint32_t metadata_in) {
    uint64_t evicted_block = evicted_addr >> LOG2_BLOCK_SIZE;

    prefetchers[cpu].eviction(evicted_block);
    return metadata_in;
}

void CACHE::prefetcher_cycle_operate() {}

void CACHE::prefetcher_final_stats() {
    // cout << "* CPU " << cpu << " Total PHT Match Probability: " << prefetchers[cpu].get_match_prob() << endl;
    prefetchers[cpu].log();
}
