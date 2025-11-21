#include "pmp_adaptive.h"
#include "custom_util.h"

#include <bits/stdc++.h>
#include <random>

#include "cache.h"
#include "ooo_cpu.h"

namespace {
	const int DEBUG_LEVEL = 0;
	bool SUPPORT_VA = false;

	// (1 << 12) >> 6 = 64
	// 64 cache blocks in a region
	constexpr int PATTERN_LEN = (1 << pmp::IN_REGION_BITS) / BLOCK_SIZE;
	constexpr int FT_SIZE = 64;
	constexpr int FT_WAY = 8;
	constexpr int AT_SIZE = 32;
	constexpr int AT_WAY = 16;
	// Offset Pattern Table
	constexpr int OPT_WAYS = 1;
	constexpr int OPT_SIZE = (1 << pmp::OFFSET_BITS) * OPT_WAYS;
	constexpr int OFFSET_MAX_CONF = 32;
	// PC Pattern Table
	constexpr int PPT_WAYS = 1;
	constexpr int PPT_SIZE = (1 << pmp::PC_BITS) * PPT_WAYS;

	constexpr int PC_MAX_CONF = 32;

	static std::vector<pmp::PMP> prefetchers;

} // namespace

// (Aditya): Implement the PrefetchBuffer::prefetch method body here in the .cc file
int pmp::PrefetchBuffer::prefetch(PMP* pmp_parent, CACHE* cache, uint64_t block_address) {
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
	for (int d = 1; d < this->pattern_len; d += 1) { // d: 1 -> 64
		for (int sgn = +1; sgn >= -1; sgn -= 2) {	 // sgn: -1, 1
			pf_offset = region_offset + sgn * d;
			if (0 <= pf_offset && pf_offset < this->pattern_len && pattern[pf_offset] > 0) {
				DEBUG(cout << pf_offset << " ";)
				uint64_t pf_address = (region_number * this->pattern_len + pf_offset) << LOG2_BLOCK_SIZE;
				// MSHR + PQ < MSHR - 1 && PQ is not full
				if (cache->get_occupancy(0, 0) < (cache->get_size(0, 0) - pmp_parent->reserved_mshrs) && cache->get_occupancy(3, 0) < cache->get_size(3, 0)) {
					uint32_t pf_metadata = 0;
					pf_metadata = __add_pf_sour_level(pf_metadata, 1);
					if (pattern[pf_offset] == 1) { // FILL_L1_PMP = 1
						pf_metadata = __add_pf_dest_level(pf_metadata, 1);
					} else {
						pf_metadata = __add_pf_dest_level(pf_metadata, 2);
					}

					int ok = cache->prefetch_line(pf_address, pattern[pf_offset] == 1 ? true : false, pf_metadata);
					pf_issued += ok;
					if (ok && !cache->warmup) {
						pmp_parent->record_prefetch_issue(pf_address);
						if (pattern[pf_offset] == 1) {
							prefetch_to_l1++;
						} else {
							prefetch_to_l2++;
						}
					}
					pattern[pf_offset] = 0;
				} else {
					DEBUG(cout << std::endl;)
					return pf_issued;
				}
			}
		}
	}
	DEBUG(cout << std::endl;)
	Super::erase(key);
	return pf_issued;
}

void pmp::PMP::access(uint64_t block_number, uint64_t pc) {
	// (Aditya): Check if the current access is a useful prefetch.
	auto* inflight_entry = this->inflight_pf_tracker.find(this->inflight_pf_tracker.build_key(block_number));
	if (inflight_entry && !inflight_entry->data.used) {
		this->useful_prefetches++;
		inflight_entry->data.used = true;
	}
	// (Aditya): End of change.

	if (this->debug_level >= 2)
		std::cerr << "[ PMP] access(block_number=0x" << std::hex << block_number << ", pc=0x" << pc << ")" << std::dec << std::endl;

	uint64_t region_number = block_number >> OFFSET_BITS;
	int region_offset = __fine_offset(block_number);
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

void pmp::PMP::eviction(uint64_t block_number) {
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

int pmp::PMP::prefetch(CACHE* cache, uint64_t block_number) {
	if (this->debug_level >= 2)
		std::cerr << " PMP::prefetch(cache=" << cache->NAME << ", block_number=" << std::hex << block_number << ")" << std::dec
				  << std::endl;
	// (Aditya): Pass 'this' to the prefetch buffer to establish a callback path.
	int pf_issued = this->pf_buffer.prefetch(this, cache, block_number);
	// (Aditya): End of change.
	if (this->debug_level >= 2)
		std::cerr << "[ PMP::prefetch] pf_issued=" << pf_issued << std::dec << std::endl;
	return pf_issued;
}

void pmp::PMP::set_debug_level(int debug_level) {
	this->filter_table.set_debug_level(debug_level);
	this->accumulation_table.set_debug_level(debug_level);
	this->opt.set_debug_level(debug_level);
	this->ppt.set_debug_level(debug_level);
	this->debug_level = debug_level;
}

void pmp::PMP::log() {
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

std::vector<int> pmp::PMP::find_in_opt(uint64_t pc, uint64_t block_number) {
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
		// better performance
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
				result_pattern[i] = pattern[i] == FILL_L1_PMP ? FILL_L2_PMP : pattern[i] == FILL_L2_PMP ? FILL_LLC_PMP
																										: 0;
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
		// (Aditya): Replaced the simplified logic with the full dual-table arbitration logic from the paper.
		// This new logic combines predictions from both OPT and PPT to improve accuracy.
		if (pattern.empty()) { // Rule 4: OPT is primary. If it has no prediction, do nothing.
			// No rotation needed, just return the empty vector.
			return result_pattern;
		}

		if (pattern_pc.empty()) { // Rule 3: PPT has no prediction, so downgrade confidence of OPT's prediction.
			for (int i = 0; i < this->pattern_len; i++) {
				if (pattern[i] == FILL_L1_PMP) {
					result_pattern[i] = FILL_L2_PMP; // Downgrade L1 -> L2
				} else if (pattern[i] == FILL_L2_PMP) {
					result_pattern[i] = FILL_LLC_PMP; // Downgrade L2 -> LLC
				} else {
					result_pattern[i] = 0;
				}
			}
		} else { // Both tables have predictions, apply arbitration rules 1 and 2.
			for (int i = 0; i < this->pattern_len; i++) {
				int opt_level = pattern[i];
				int ppt_level = pattern_pc[i / PATTERN_DEGRADE_LEVEL]; // Map to the coarse PPT pattern

				if (opt_level == FILL_L1_PMP && ppt_level == FILL_L1_PMP) {
					// Rule 1: Both tables agree on L1D prefetch. High confidence.
					result_pattern[i] = FILL_L1_PMP;
				} else if (opt_level > 0 && ppt_level > 0) {
					// Rule 2: Both tables predict a prefetch, but not for L1D. Use L2C.
					result_pattern[i] = FILL_L2_PMP;
				} else if (opt_level > 0 && ppt_level == 0) {
					// Part of Rule 3: OPT predicts, but this specific PC's pattern doesn't confirm. Downgrade.
					if (opt_level == FILL_L1_PMP) {
						result_pattern[i] = FILL_L2_PMP;
					} else if (opt_level == FILL_L2_PMP) {
						result_pattern[i] = FILL_LLC_PMP;
					}
				} else {
					// Rule 4: If OPT has no prediction for this offset, we don't prefetch it, even if PPT does.
					result_pattern[i] = 0;
				}
			}
		}
		// (Aditya): End of change.
#endif
	}

	int offset = __coarse_offset(__fine_offset(block_number));
	result_pattern = custom_util::my_rotate(result_pattern, +offset);
	return result_pattern;
}

void pmp::PMP::insert_in_opt(const pmp::AccumulationTable::Entry& entry) {
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

std::vector<int> pmp::PMP::vote(const std::vector<pmp::OffsetPatternTableData>& x, bool is_pc_opt) {
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

// (Aditya): Implement the adaptive threshold feedback loop and prefetch recording.
void pmp::PMP::record_prefetch_issue(uint64_t pf_addr) {
	uint64_t pf_block = pf_addr >> LOG2_BLOCK_SIZE;
	auto evicted = this->inflight_pf_tracker.insert(this->inflight_pf_tracker.build_key(pf_block), {});
	if (evicted.valid && !evicted.data.used) {
		// An unused prefetch was evicted from our tracker, count it as useless
		this->useless_prefetches++;
	}
}

void pmp::PMP::cycle_operate() {
	// Define constants for the adaptive mechanism
	const uint64_t ADAPTIVE_INTERVAL = 10000;
	const double HIGH_ACCURACY_TARGET = 0.75;
	const double LOW_ACCURACY_TARGET = 0.40;
	const double THRESHOLD_STEP = 0.01;
	const double MAX_L1D_THRESH = 0.90;
	const double MIN_L1D_THRESH = 0.10;

	cycle_count++;
	if (cycle_count < ADAPTIVE_INTERVAL) {
		return;
	}

	// Interval reached, perform adaptation
	uint64_t total_evaluated = useful_prefetches + useless_prefetches;
	if (total_evaluated > 50) { // Only adapt if we have a meaningful number of samples
		double current_accuracy = (double)useful_prefetches / total_evaluated;

		if (current_accuracy > HIGH_ACCURACY_TARGET) {
			// Too conservative, get more aggressive
			this->L1D_THRESH = std::max(MIN_L1D_THRESH, this->L1D_THRESH - THRESHOLD_STEP);
			this->reserved_mshrs = 1; // High accuracy -> Be aggressive
		} else if (current_accuracy < LOW_ACCURACY_TARGET) {
			// Too aggressive, get more conservative
			this->L1D_THRESH = std::min(MAX_L1D_THRESH, this->L1D_THRESH + THRESHOLD_STEP);
			this->reserved_mshrs = 4; // Low accuracy -> Be conservative
		} else {
			this->reserved_mshrs = 2; // Moderate accuracy -> Default
		}

		// Update L2C threshold to be proportional
		this->L2C_THRESH = this->L1D_THRESH * this->L2C_THRESH_RATIO;
	}

	// Reset for the next interval
	this->useful_prefetches = 0;
	this->useless_prefetches = 0;
	this->cycle_count = 0;
}
// (Aditya): End of change.

void CACHE::prefetcher_initialize() {
	std::cout << NAME << " PMP prefetcher" << std::endl;
	prefetchers = std::vector<pmp::PMP>(NUM_CPUS,
		pmp::PMP(PATTERN_LEN, pmp::OFFSET_BITS, OPT_SIZE, OFFSET_MAX_CONF, OPT_WAYS, pmp::PC_BITS, PPT_SIZE,
			PC_MAX_CONF, PPT_WAYS, FT_SIZE, FT_WAY, AT_SIZE, AT_WAY, pmp::PF_BUFFER_SIZE, pmp::PF_BUFFER_WAY,
			FILL_L1, FILL_L2, FILL_LLC,
			DEBUG_LEVEL,
			cpu));
}

uint32_t CACHE::prefetcher_cache_operate(uint64_t addr, uint64_t ip, uint8_t cache_hit, uint8_t type, uint32_t metadata_in) {
	if (DEBUG_LEVEL >= 2) {
		std::cerr << "CACHE::l1d_prefetcher_operate(addr=0x" << std::hex << addr << ", ip=0x" << ip << ", cache_hit=" << std::dec
				  << (int)cache_hit << ", type=" << (int)type << ")" << std::dec << std::endl;
		std::cerr << "[CACHE::l1d_prefetcher_operate] CACHE{core=" << this->cpu << ", NAME=" << this->NAME << "}" << std::dec
				  << std::endl;
	}

	if (type != LOAD)
		return metadata_in;

	uint64_t block_number = addr >> pmp::BOTTOM_BITS;

	prefetchers[cpu].access(block_number, ip);

	prefetchers[cpu].prefetch(this, block_number);

	if (DEBUG_LEVEL >= 3) {
		prefetchers[cpu].log();
		std::cerr << "=======================================" << std::dec << std::endl;
	}
	return metadata_in;
}

uint32_t CACHE::prefetcher_cache_fill(uint64_t addr, uint32_t set, uint32_t way, uint8_t prefetch, uint64_t evicted_addr, uint32_t metadata_in) {
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
	// (Aditya): Call the prefetcher's cycle_operate to run the adaptive logic.
	prefetchers[cpu].cycle_operate();
	// (Aditya): End of change.
}

void CACHE::prefetcher_final_stats() {
	std::cout << "Prefetch Request to L1: " << pmp::prefetch_to_l1 << ", "
			  << "Prefetch Request to L2: " << pmp::prefetch_to_l2 << std::endl;
	std::cout << "Invalid by Eviction: " << prefetchers[cpu].invalid_by_eviction << std::endl;
	std::cout << "Invalid by Max: " << prefetchers[cpu].invalid_by_max << std::endl;
	prefetchers[cpu].log();

	std::cout << "Filter by PPT: " << pmp::filter_by_ppt << std::endl;
}
