#include "gaze.h"
#include "cache.h"

#include <assert.h>

// pf_metadata: 0 stride, 1 dpt, 2 spt

static std::vector<gaze::Gaze> prefetchers;
static int trigger_con[gaze::NUM_BLOCKS] = {0};
#ifdef TRACK_OOO_EFFECT
extern std::map<uint64_t, std::pair<uint64_t, uint64_t>> ooo_effect_tracker;
#endif

int n_effected_by_ooo = 0;
int n_not_effected_by_ooo = 0;

namespace {

constexpr int FT_SIZE = 64;
constexpr int FT_WAY = 8;
constexpr int AT_SIZE = 64;
constexpr int AT_WAY = 8;
constexpr int PT_WAY = 4;
constexpr int PT_SIZE = PT_WAY * gaze::NUM_BLOCKS;
constexpr int PB_SIZE = 32;
constexpr int PB_WAY = 8;
} // namespace

namespace gaze {

void Gaze::access(uint64_t block_num, uint64_t pc, CACHE* cache) {
    uint64_t region_num = block_num >> (LOG2_REGION_SIZE - LOG2_BLOCK_SIZE);
    uint64_t region_offset = __region_offset(block_num);
    auto at_entry = this->at.set_pattern(region_num, region_offset);
    if (at_entry) {
        if (at.get_stride_prefetch()) {
            int stride = at_entry->data.last_stride;
            int begin_offset = at_entry->data.last_offset;
            at_entry->data.last_offset = at_entry->data.last_stride = 0;
            std::vector<int> pattern(NUM_BLOCKS, 0);
            for (int i = 1; i <= stride_pf_degree; i++) {
                if (begin_offset + (i + STRIDE_PF_LOOKAHEAD) * stride < NUM_BLOCKS && begin_offset + (i + STRIDE_PF_LOOKAHEAD) * stride >= 0) {
                    if (!(at_entry->data.pattern[begin_offset + (i + STRIDE_PF_LOOKAHEAD) * stride]))
                        pattern[begin_offset + (i + STRIDE_PF_LOOKAHEAD) * stride] = PF_FILL_L1;
                }
            }
            if (at_entry->data.missed_in_pt)
                pb.insert(region_num, pattern, begin_offset, begin_offset, 0);
            else if (at_entry->data.con)
                pb.insert(region_num, pattern, begin_offset, begin_offset, 3);
            at.turn_off_stride_prefetch();
        }
        return;
    } else {
        auto entry = ft.find(region_num);
        if (!entry) {
            ft.insert(region_num, region_offset, pc);
            return;
        } else if (entry->data.trigger_offset != region_offset) { // SECOND OFFSET

#ifdef TRACK_OOO_EFFECT
            if (!warmup) {
                if (ooo_effect_tracker.find(block_num >> 6) != ooo_effect_tracker.end()) {
                    auto [trigger_offset, second_offset] = ooo_effect_tracker.at(block_num >> 6);
                    assert(second_offset != std::numeric_limits<uint64_t>::max());
                    if ((second_offset == region_offset && trigger_offset == entry->data.trigger_offset) || (second_offset == entry->data.trigger_offset && trigger_offset == region_offset)) {
                        n_not_effected_by_ooo++;
                    } else {
                        // std::cout << trigger_offset << " " << second_offset << ", " << entry->data.trigger_offset << " " << region_offset << std::endl;
                        n_effected_by_ooo++;
                    }
                    ooo_effect_tracker.erase(block_num >> 6);
                } else {
                    // assert(0);
                }
            }
#endif

            // 1. find pattern
            auto pt_entry = find_in_pt(entry->data.trigger_offset, region_offset, pc, region_num);
            // pattern empty?
            bool pattern_empty = (!pt_entry) || (2 == std::count_if(pt_entry->data.pattern.begin(), pt_entry->data.pattern.end(), [](auto& x) { return x != 0; }));
            bool all_set = pattern_empty ? false : pattern_all_set(pt_entry->data.pattern);

            if (!pattern_empty) {
                uint32_t pf_metadata = pt_entry->data.con ? 2 : 1;
                pb.insert(region_num, pt_entry->data.pattern, entry->data.trigger_offset, region_offset, pf_metadata);
                if (!pt_entry->data.con)
                    trigger_con[entry->data.trigger_offset]++;
            }

            // 2. insert into at
            auto at_victim = at.insert(region_num, entry->data.trigger_offset, region_offset, entry->data.pc, pattern_empty, (!pattern_empty) && pt_entry->data.con);
            if (ft.erase(region_num))
                ft.increase_ft_valid_entry_eviction();
            if (at_victim.valid) {
                insert_in_pt(at_victim, region_num);
            }
        }
    }
}

void Gaze::eviction(uint64_t block_num) {
    uint64_t region_num = block_num >> (LOG2_REGION_SIZE - LOG2_BLOCK_SIZE);
    if (ft.erase(region_num))
        ft.increase_ft_invalid_entry_eviction();
    auto entry = at.erase(region_num);
    if (entry) {
        insert_in_pt(*entry, region_num);
    }
}

void Gaze::prefetch(CACHE* cache, uint64_t block_num) {
    pb.prefetch(cache, block_num);
}

void Gaze::log() {
    std::cout << "Filter table begin" << std::dec << std::endl;
    std::cout << this->ft.log();
    std::cout << "Filter table end" << std::endl;

    std::cout << "Accumulation table begin" << std::dec << std::endl;
    std::cout << this->at.log();
    std::cout << "Accumulation table end" << std::endl;

    std::cout << "Pattern table begin" << std::dec << std::endl;
    std::cout << this->pt.log();
    std::cout << "Pattern table end" << std::endl;

    std::cout << "Prefetch buffer begin" << std::dec << std::endl;
    std::cout << this->pb.log();
    std::cout << "Prefetch buffer end" << std::endl;
}

void Gaze::tune_stride_degree(CACHE* cache) {
}

std::pair<float, float> calculate_acc_and_cov(std::vector<int> pattern_1, std::vector<int> pattern_2) {
    uint64_t num_bits_1 = 0, num_bits_2 = 0, num_same = 0;

    for (int i = 0; i < NUM_BLOCKS; i++) {
        if (pattern_1[i] != 0)
            num_bits_1++;
        if (pattern_2[i] != 0)
            num_bits_2++;
        if (pattern_1[i] != 0 || pattern_2[i] != 0) {
            if (pattern_1[i] != 0 && pattern_2[i] != 0)
                num_same++;
        }
    }

    return {(float)num_same / num_bits_1, (float)num_same / num_bits_2};
}

bool different_patterns(std::vector<int> pattern_1, std::vector<int> pattern_2) {
    auto [acc, cov] = calculate_acc_and_cov(pattern_1, pattern_2);
    if (cov < 0.25)
        return true;
    return false;
}

std::vector<int> pattern_bool2int(std::vector<bool> pattern) {
    std::vector<int> pattern_int(NUM_BLOCKS, 0);
    for (int i = 0; i < NUM_BLOCKS; i++)
        pattern_int[i] = (pattern[i] ? PF_FILL_L1 : 0);
    return pattern_int;
}

bool pattern_all_set(std::vector<bool> pattern) {
    for (int i = 0; i < NUM_BLOCKS; i++)
        if (!pattern[i])
            return false;
    return true;
}

bool pattern_all_set(std::vector<int> pattern) {
    for (int i = 0; i < NUM_BLOCKS; i++)
        if (pattern[i] == 0)
            return false;
    return true;
}
} // namespace gaze

void CACHE::prefetcher_initialize() {
    std::cout << NAME << " Gaze NEW NEW prefetcher" << std::endl;

    prefetchers = std::vector<gaze::Gaze>(
        NUM_CPUS, gaze::Gaze(FT_SIZE, FT_WAY, AT_SIZE, AT_WAY, PT_SIZE, PT_WAY, PB_SIZE, PB_WAY, cpu));
}

uint32_t CACHE::prefetcher_cache_operate(uint64_t addr, uint64_t ip, uint8_t cache_hit, uint8_t type, uint32_t metadata_in) {
    uint64_t line_addr = (addr >> LOG2_BLOCK_SIZE); // Line addr
    uint64_t region_num = (addr >> LOG2_PAGE_SIZE);
    int offset = line_addr % gaze::NUM_BLOCKS;
    if (!warmup) {
        if (type == LOAD) {
            if (region_map_load.find(region_num) == region_map_load.end()) {
                region_map_load.insert({region_num, std::vector<int>(gaze::NUM_BLOCKS, 0)});
            }
            region_map_load.at(region_num)[offset] = 1; // load
        }
    }

    prefetchers[cpu].set_warmup(warmup);

    // std::cout << (unsigned int)type << " " << champsim::to_underlying(access_type::LOAD) << std::endl;
    if (type != LOAD)
        return metadata_in;
    uint64_t block_num = addr >> LOG2_BLOCK_SIZE;

    prefetchers[cpu].access(block_num, ip, this);
    prefetchers[cpu].prefetch(this, block_num);

    return metadata_in;
}

uint32_t CACHE::prefetcher_cache_fill(uint64_t addr, uint32_t set, uint32_t way, uint8_t prefetch, uint64_t evicted_addr, uint32_t metadata_in) {
    uint64_t evicted_block_num = evicted_addr >> LOG2_BLOCK_SIZE;

    // prefetchers[cpu].eviction(evicted_block_num);

    return metadata_in;
}

void CACHE::prefetcher_cycle_operate() {
}

void CACHE::prefetcher_final_stats() {
    std::cout << n_effected_by_ooo << " " << n_not_effected_by_ooo << " " << (double)n_effected_by_ooo / (n_effected_by_ooo + n_not_effected_by_ooo) << std::endl;

    std::cout
        << "Num Dis Issued from prefetcher: " << prefetchers[cpu].get_pb().num_dis_issued_regions << ", "
        << "Num Con Issued from prefetcher: " << prefetchers[cpu].get_pb().num_con_issued_regions << ", "
        << "Num Stride Issued from prefetcher: " << prefetchers[cpu].get_pb().num_stride_issued_regions << std::endl;

    std::cout << "Num Dis Filled: " << num_fill_gaze[1] << ", "
              << "Num Con Filled: " << num_fill_gaze[2] << ", "
              << "Num Stride Filled: " << num_fill_gaze[0] << ", "
              << "Num Promoted Filled: " << num_fill_gaze[3] << std::endl;

    std::cout << "Num Dis Useful: " << num_useful_gaze[1] << " Useless:" << num_useless_gaze[1] << " Accuracy: " << (100 * (double)num_useful_gaze[1] / (num_useful_gaze[1] + num_useless_gaze[1])) << ", "
              << "Num Con Useful: " << num_useful_gaze[2] + num_useful_gaze[3] << " Useless:" << num_useless_gaze[2] + num_useless_gaze[3] << " Accuracy: " << (100 * ((double)num_useful_gaze[2] + num_useful_gaze[3]) / (num_useful_gaze[2] + num_useless_gaze[2] + num_useful_gaze[3] + num_useless_gaze[3])) << ", "
              << "Num Stride Useful: " << num_useful_gaze[0] << " Useless:" << num_useless_gaze[0] << " Accuracy: " << (100 * (double)num_useful_gaze[0] / (num_useful_gaze[0] + num_useless_gaze[0])) << ", "
              << "Num Promoted Useful: " << num_useful_gaze[3] << " Useless:" << num_useless_gaze[3] << " Accuracy: " << (100 * (double)num_useful_gaze[3] / (num_useful_gaze[3] + num_useless_gaze[3])) << std::endl;

    std::cout << "Prefetch Request to L1: " << prefetchers[cpu].get_pb().prefetch_to_l1 << ", "
              << "Prefetch Request to L2: " << prefetchers[cpu].get_pb().prefetch_to_l2 << std::endl;

    int num_dense = 0;
    int num_dense_all_covered = 0;
    int num_dense_uncovered = 0;
    std::vector<uint64_t> dense_regions;
    for (auto r : region_map_load) {
        if (std::count_if(r.second.begin(), r.second.end(), [](auto l) { return l == 1; }) == 64) {
            dense_regions.push_back(r.first);
        }
    }

    for (auto r : dense_regions) {
        if (region_map_pref.find(r) == region_map_pref.end()) {
            num_dense_uncovered += 64;
            continue;
        }
        num_dense_uncovered += std::count_if(region_map_pref.at(r).begin(), region_map_pref.at(r).end(), [](auto l) { return l == 0; });
    }

    std::cout << "total region: " << region_map_load.size() << ", Dense Rate: " << (double)(dense_regions.size()) / region_map_load.size() << ", AVG Uncovered per Dense Region: " << (double)num_dense_uncovered / dense_regions.size() << std::endl;

    prefetchers[cpu].log();
}