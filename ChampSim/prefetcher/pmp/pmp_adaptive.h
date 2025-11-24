#ifndef PMP_H
#define PMP_H

#include "cache.h"
#include "custom_util.h"

#include <bits/stdc++.h>
#include <random>
#include <stdint.h>

namespace pmp {

	// (Aditya): Forward-declare PMP class for the callback pointer.
	class PMP;
	// (Aditya): Moved constants from pmp.cc to make them visible in the header.
	constexpr int PF_BUFFER_SIZE = 32;
	constexpr int PF_BUFFER_WAY = 8;
	// (Aditya): End of change.

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

	// (Aditya): A tracker for in-flight prefetches to measure accuracy.
	class InflightPFData {
	public:
		bool used = false;
		// (Manish)
		uint64_t issue_cycle = 0;  // Track when prefetch was issued
	};

	class InflightPFTracker : public custom_util::LRUSetAssociativeCache<InflightPFData> {
		typedef custom_util::LRUSetAssociativeCache<InflightPFData> Super;

	public:
		InflightPFTracker(int size, int num_ways) : Super(size, num_ways) {}

		void write_data(Entry& entry, custom_util::Table& table, int row) override {
			table.set_cell(row, 0, entry.key);
			table.set_cell(row, 1, entry.data.used);
		}

		uint64_t build_key(uint64_t key) {
			return custom_util::hash_index(key, this->index_len);
		}
	};
	// (Aditya): End of change.

	int filter_by_ppt = 0;
	int prefetch_to_l1, prefetch_to_l2 = 0;

	// SMS Filter Table Data
	// <Tag, PC/Offset>
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
		// std::vector<int> new_pattern;
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

		void insert(uint64_t address, uint64_t pc, std::vector<bool> pattern, bool is_degrade, int second_offset) {
			if (this->debug_level >= 2)
				std::cerr << "OffsetPatternTable::insert(" << std::hex << "address=0x" << address
						  << ", pattern=" << custom_util::pattern_to_string(pattern) << ")" << std::dec << std::endl;
			int offset = __coarse_offset(__fine_offset(address));
			offset = is_degrade ? offset / PATTERN_DEGRADE_LEVEL : offset;
			pattern = custom_util::my_rotate(pattern, -offset);
			// auto new_pattern = pattern;
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

	class PMP {
	public:
		PMP(int pattern_len, int offset_width, int opt_size, int opt_max_conf, int opt_ways, int pc_width,
			int ppt_size, int ppt_max_conf, int ppt_ways, int filter_table_size, int ft_way,
			int accumulation_table_size, int at_way, int pf_buffer_size, int pf_buffer_way,
			int FILL_L1, int FILL_L2, int FILL_LLC,
			int debug_level = 0, int cpu = 0) : pattern_len(pattern_len), opt(opt_size, pattern_len, offset_width, opt_ways, opt_max_conf, debug_level, cpu), ppt(ppt_size, pattern_len / PATTERN_DEGRADE_LEVEL, pc_width, ppt_ways, ppt_max_conf, debug_level, cpu), filter_table(filter_table_size, debug_level, ft_way), accumulation_table(accumulation_table_size, pattern_len, debug_level, at_way), pf_buffer(pf_buffer_size, pattern_len, debug_level, pf_buffer_way)
											  // (Aditya): Initialize adaptive thresholds and the in-flight tracker.
											  , L1D_THRESH(0.50)
											  , L2C_THRESH(0.150)
											  , inflight_pf_tracker(pf_buffer_size * 8, pf_buffer_way * 4) // (Manish) //Was *2, *2
											  // (Aditya): End of change.
											  , FILL_L1_PMP(1)
											  , FILL_L2_PMP(2)
											  , FILL_LLC_PMP(3)
											  , debug_level(debug_level)
											  , cpu(cpu) {
			if (this->debug_level >= 1)
				std::cerr << " PMP:: PMP(pattern_len=" << pattern_len
						  << ", filter_table_size=" << filter_table_size
						  << ", accumulation_table_size=" << accumulation_table_size
						  << ", pf_buffer_size=" << pf_buffer_size
						  << ", debug_level=" << debug_level << ")" << std::endl;
		}

		void access(uint64_t block_number, uint64_t pc);
		void eviction(uint64_t block_number);
		int prefetch(CACHE* cache, uint64_t block_number);
		void set_debug_level(int debug_level);
		void log();

		// (Aditya): Add public methods for the adaptive feedback loop.
		void cycle_operate();
		void record_prefetch_issue(uint64_t pf_addr);
		void record_prefetch_eviction(uint64_t pf_addr);  // (Manish) NEW: Track evictions
		// (Aditya): End of change.

		int FILL_L1_PMP;
		int FILL_L2_PMP;
		int FILL_LLC_PMP;
		int invalid_by_eviction = 0;
		int invalid_by_max = 0;

		// (Manish)
		// IMPROVED: Percentage-based MSHR reservation instead of fixed slots
		double demand_reserve_pct = 0.25; // Reserve 25% of MSHRs for demand misses
		
		// Track demand pressure for adaptive reservation
		uint64_t demand_miss_blocked_count = 0;
		uint64_t demand_miss_total_count = 0;
		double L1D_THRESH;
		double L2C_THRESH;
		const double LLC_THRESH = 1; /* off */
		// (Manish) Ends here

	private:
		std::vector<int>
		find_in_opt(uint64_t pc, uint64_t block_number);
		void insert_in_opt(const AccumulationTable::Entry& entry);
		std::vector<int> vote(const std::vector<OffsetPatternTableData>& x, bool is_pc_opt = false);

		// (Aditya): Make thresholds non-const and add members for the adaptive mechanism.
		

		const double PC_L1D_THRESH = 0.50;
		const double PC_L2C_THRESH = 0.150;
		const double PC_LLC_THRESH = 1; /* off */

		/*======================*/

		int pattern_len;
		FilterTable filter_table;
		AccumulationTable accumulation_table;
		OffsetPatternTable opt;
		PCPatternTable ppt;
		PrefetchBuffer pf_buffer;
		int debug_level = 0;
		int cpu;

		// Adaptive mechanism members
		uint64_t cycle_count = 0;
		uint64_t useful_prefetches = 0;
		uint64_t useless_prefetches = 0;
		InflightPFTracker inflight_pf_tracker;
		const double L2C_THRESH_RATIO = 0.3; // Keep L2C threshold proportional to L1D's

		// (Aditya): End of change.

		// (Manish) :		
		// NEW: Constants for adaptive mechanism
		static constexpr uint64_t PREFETCH_TIMEOUT_CYCLES = 50000; // Timeout for stale prefetches
		// (Manish) : End of change
	};

} // namespace pmp

#endif
