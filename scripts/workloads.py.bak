import random
import math

workloads_spec06 = [
    ['410.bwaves-1963B.champsimtrace.xz', '410_1963'], ['410.bwaves-2097B.champsimtrace.xz', '410_2097'], ['429.mcf-22B.champsimtrace.xz', '429_22'], 
    ['429.mcf-51B.champsimtrace.xz', '429_51'], ['429.mcf-184B.champsimtrace.xz', '429_184'], ['429.mcf-192B.champsimtrace.xz', '429_192'], 
    ['433.milc-127B.champsimtrace.xz', '433_127'], ['433.milc-337B.champsimtrace.xz', '433_337'], 
    ['436.cactusADM-1804B.champsimtrace.xz', '436_1804'], 
    ['437.leslie3d-271B.champsimtrace.xz', '437_271'], ['437.leslie3d-134B.champsimtrace.xz', '437_134'], ['437.leslie3d-149B.champsimtrace.xz', '437_149'], ['437.leslie3d-232B.champsimtrace.xz', '437_232'], ['437.leslie3d-265B.champsimtrace.xz', '437_265'], ['437.leslie3d-273B.champsimtrace.xz', '437_273'],
    ['450.soplex-92B.champsimtrace.xz', '450_92'], ['450.soplex-247B.champsimtrace.xz', '450_247'], 
    ['459.GemsFDTD-1211B.champsimtrace.xz', '459_1211'], ['459.GemsFDTD-765B.champsimtrace.xz', '459_765'], ['459.GemsFDTD-1169B.champsimtrace.xz', '459_1169'], ['459.GemsFDTD-1418B.champsimtrace.xz', '459_1418'], ['459.GemsFDTD-1491B.champsimtrace.xz', '459_1491'],
    ['462.libquantum-714B.champsimtrace.xz', '462_714'], ['462.libquantum-1343B.champsimtrace.xz', '462_1343'], 
    ['470.lbm-1274B.champsimtrace.xz', '470_1274'],
    ['471.omnetpp-188B.champsimtrace.xz', '471_188'], 
    ['473.astar-359B.champsimtrace.xz', '473_359'], 
    ['481.wrf-196B.champsimtrace.xz', '481_196'], ['481.wrf-455B.champsimtrace.xz', '481_455'], ['481.wrf-816B.champsimtrace.xz', '481_816'], ['481.wrf-1254B.champsimtrace.xz', '481_1254'], ['481.wrf-1281B.champsimtrace.xz', '481_1281'], 
    ['482.sphinx3-234B.champsimtrace.xz', '482_234'], ['482.sphinx3-417B.champsimtrace.xz', '482_417'], ['482.sphinx3-1100B.champsimtrace.xz', '482_1100'], ['482.sphinx3-1297B.champsimtrace.xz', '482_1297'], ['482.sphinx3-1395B.champsimtrace.xz', '482_1395'], ['482.sphinx3-1522B.champsimtrace.xz', '482_1522'],
    ['483.xalancbmk-127B.champsimtrace.xz', '483_127'],
]

workloads_spec17 = [
    ['602.gcc_s-734B.champsimtrace.xz', '602_734'], ['602.gcc_s-1850B.champsimtrace.xz', '602_1850'], ['602.gcc_s-2226B.champsimtrace.xz', '602_2226'],
    ['603.bwaves_s-1740B.champsimtrace.xz', '603_1740'], ['603.bwaves_s-2609B.champsimtrace.xz', '603_2609'], ['603.bwaves_s-2931B.champsimtrace.xz', '603_2931'],
    ['605.mcf_s-484B.champsimtrace.xz', '605_484'], ['605.mcf_s-665B.champsimtrace.xz', '605_665'], ['605.mcf_s-782B.champsimtrace.xz', '605_782'], ['605.mcf_s-472B.champsimtrace.xz', '605_472'], ['605.mcf_s-994B.champsimtrace.xz', '605_994'], ['605.mcf_s-1536B.champsimtrace.xz', '605_1536'], ['605.mcf_s-1554B.champsimtrace.xz', '605_1554'], ['605.mcf_s-1644B.champsimtrace.xz', '605_1644'],
    ['607.cactuBSSN_s-3477B.champsimtrace.xz', '607_3477'], ['607.cactuBSSN_s-4004B.champsimtrace.xz', '607_4004'], ['607.cactuBSSN_s-2421B.champsimtrace.xz', '607_2421'],
    ['619.lbm_s-2676B.champsimtrace.xz', '619_2676'], ['619.lbm_s-2677B.champsimtrace.xz', '619_2677'], ['619.lbm_s-3766B.champsimtrace.xz', '619_3766'], ['619.lbm_s-4268B.champsimtrace.xz', '619_4268'],
    ['620.omnetpp_s-141B.champsimtrace.xz', '620_141'], ['620.omnetpp_s-874B.champsimtrace.xz', '620_874'], 
    ['621.wrf_s-6673B.champsimtrace.xz', '621_6673'], ['621.wrf_s-8065B.champsimtrace.xz', '621_8065'],
    ['623.xalancbmk_s-10B.champsimtrace.xz', '623_10'], ['623.xalancbmk_s-202B.champsimtrace.xz', '623_202'],
    ['627.cam4_s-490B.champsimtrace.xz', '627_490'],
    ['628.pop2_s-17B.champsimtrace.xz', '628_17'], 
    ['649.fotonik3d_s-1176B.champsimtrace.xz', '649_1176'], ['649.fotonik3d_s-7084B.champsimtrace.xz', '649_7084'], ['649.fotonik3d_s-8225B.champsimtrace.xz', '649_8225'], ['649.fotonik3d_s-10881B.champsimtrace.xz', '649_10881'],
    ['654.roms_s-293B.champsimtrace.xz', '654_293'], ['654.roms_s-294B.champsimtrace.xz', '654_294'], ['654.roms_s-523B.champsimtrace.xz', '654_523'], ['654.roms_s-1007B.champsimtrace.xz', '654_1007'], ['654.roms_s-1070B.champsimtrace.xz', '654_1070'], ['654.roms_s-1390B.champsimtrace.xz', '654_1390'],
]

workloads_ligra = [
    ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_51000M.length_250M.champsimtrace.xz', 'lig_pr_51000'], 
    ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_79500M.length_250M.champsimtrace.xz', 'lig_pr_79500'], 
    ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_18500M.length_250M.champsimtrace.xz', 'lig_pr_18500'],
    ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_21750M.length_250M.champsimtrace.xz', 'lig_pr_21750'],
    ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_pr_5000'],
    ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_500M.length_250M.champsimtrace.xz', 'lig_pr_500'],
    ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_60750M.length_250M.champsimtrace.xz', 'lig_pr_60750'],

    ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_1250M.length_250M.champsimtrace.xz', 'lig_pa_1250'], 
    ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_pa_3500'], 
    ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_6000M.length_250M.champsimtrace.xz', 'lig_pa_6000'], 
    ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_17000M.length_250M.champsimtrace.xz', 'lig_pa_17000'], 
    ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_24000M.length_250M.champsimtrace.xz', 'lig_pa_24000'], 
    ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_24500M.length_250M.champsimtrace.xz', 'lig_pa_24500'], 
    ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_35250M.length_250M.champsimtrace.xz', 'lig_pa_35250'], 
    ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_52000M.length_250M.champsimtrace.xz', 'lig_pa_52000'], 

    ['ligra_Triangle.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M.champsimtrace.xz', 'lig_tr_750'], 
    ['ligra_Triangle.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_tr_3500'], 
    ['ligra_Triangle.com-lj.ungraph.gcc_6.3.0_O3.drop_6000M.length_250M.champsimtrace.xz', 'lig_tr_6000'], 

    ['ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_26750M.length_250M.champsimtrace.xz', 'lig_bc_26750'], 
    ['ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_15750M.length_250M.champsimtrace.xz', 'lig_bc_15750'], 
    ['ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_15500M.length_250M.champsimtrace.xz', 'lig_bc_15500'], 
    ['ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_bc_5000'], 
    ['ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_bc_3500'], 
    ['ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_500M.length_250M.champsimtrace.xz', 'lig_bc_500'], 

    ['ligra_BellmanFord.com-lj.ungraph.gcc_6.3.0_O3.drop_4000M.length_250M.champsimtrace.xz', 'lig_bf_4000'], 
    ['ligra_BellmanFord.com-lj.ungraph.gcc_6.3.0_O3.drop_5500M.length_250M.champsimtrace.xz', 'lig_bf_5500'], 
    ['ligra_BellmanFord.com-lj.ungraph.gcc_6.3.0_O3.drop_24750M.length_250M.champsimtrace.xz', 'lig_bf_24750'], 
    ['ligra_BellmanFord.com-lj.ungraph.gcc_6.3.0_O3.drop_33750M.length_250M.champsimtrace.xz', 'lig_bf_33750'], 

    ['ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_18000M.length_250M.champsimtrace.xz', 'lig_bb_18000'], 
    ['ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_23000M.length_250M.champsimtrace.xz', 'lig_bb_23000'], 
    ['ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_2500M.length_250M.champsimtrace.xz', 'lig_bb_2500'], 
    ['ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_500M.length_250M.champsimtrace.xz', 'lig_bb_500'], 

    ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_15500M.length_250M.champsimtrace.xz', 'lig_bs_15500'], 
    ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_17000M.length_250M.champsimtrace.xz', 'lig_bs_17000'], 
    ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_18750M.length_250M.champsimtrace.xz', 'lig_bs_18750'], 
    ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_22000M.length_250M.champsimtrace.xz', 'lig_bs_22000'], 
    ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_bs_3500'], 
    ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_bs_5000'], 
    ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M.champsimtrace.xz', 'lig_bs_750'], 

    ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_15750M.length_250M.champsimtrace.xz', 'lig_bfs_15750'], 
    ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_17000M.length_250M.champsimtrace.xz', 'lig_bfs_17000'], 
    ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_20250M.length_250M.champsimtrace.xz', 'lig_bfs_20250'], 
    ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_21500M.length_250M.champsimtrace.xz', 'lig_bfs_21500'], 
    ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_bfs_3500'], 
    ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_bfs_5000'], 
    ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_500M.length_250M.champsimtrace.xz', 'lig_bfs_500'], 

    ['ligra_CF.com-lj.ungraph.gcc_6.3.0_O3.drop_154750M.length_250M.champsimtrace.xz', 'lig_cf_154750'], 
    ['ligra_CF.com-lj.ungraph.gcc_6.3.0_O3.drop_184750M.length_250M.champsimtrace.xz', 'lig_cf_184750'], 
    ['ligra_CF.com-lj.ungraph.gcc_6.3.0_O3.drop_2500M.length_250M.champsimtrace.xz', 'lig_cf_2500'], 
        
    ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_15750M.length_250M.champsimtrace.xz', 'lig_cp_15750'], 
    ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_18000M.length_250M.champsimtrace.xz', 'lig_cp_18000'], 
    ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_22750M.length_250M.champsimtrace.xz', 'lig_cp_22750'], 
    ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_23750M.length_250M.champsimtrace.xz', 'lig_cp_23750'], 
    ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_cp_3500'], 
    ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_cp_5000'], 
    ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M.champsimtrace.xz', 'lig_cp_750'], 

    ['ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_21000M.length_250M.champsimtrace.xz', 'lig_cps_21000'], 
    ['ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_22000M.length_250M.champsimtrace.xz', 'lig_cps_22000'], 
    ['ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_cps_3500'], 
    ['ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_cps_5000'], 
    ['ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M.champsimtrace.xz', 'lig_cps_750'], 
        
    ['ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_15750M.length_250M.champsimtrace.xz', 'lig_mis_15750'], 
    ['ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_17000M.length_250M.champsimtrace.xz', 'lig_mis_17000'], 
    ['ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_21250M.length_250M.champsimtrace.xz', 'lig_mis_21250'], 
    ['ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_mis_3500'], 
    ['ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_mis_5000'], 
    ['ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M.champsimtrace.xz', 'lig_mis_750'], 
]

workloads_parsec = [
    ['parsec_2.1.canneal.simlarge.prebuilt.drop_500M.length_250M.champsimtrace.xz', 'par_ca_500'], 
    ['parsec_2.1.facesim.simlarge.prebuilt.drop_1500M.length_250M.champsimtrace.xz', 'par_fs_1500'], 
    ['parsec_2.1.facesim.simlarge.prebuilt.drop_21500M.length_250M.champsimtrace.xz', 'par_fs_21500'], 
    ['parsec_2.1.streamcluster.simlarge.prebuilt.drop_4750M.length_250M.champsimtrace.xz', 'par_sc_4750'], 
]

workloads_cloudsuite = [
    ['cassandra_phase0_core0.trace.xz', 'cass_p0_c0'], ['cassandra_phase0_core1.trace.xz', 'cass_p0_c1'], ['cassandra_phase0_core2.trace.xz', 'cass_p0_c2'], ['cassandra_phase0_core3.trace.xz', 'cass_p0_c3'],
    ['cassandra_phase1_core0.trace.xz', 'cass_p1_c0'], ['cassandra_phase1_core1.trace.xz', 'cass_p1_c1'], ['cassandra_phase1_core2.trace.xz', 'cass_p1_c2'], ['cassandra_phase1_core3.trace.xz', 'cass_p1_c3'],
    ['cassandra_phase2_core1.trace.xz', 'cass_p2_c1'], ['cassandra_phase2_core2.trace.xz', 'cass_p2_c2'], ['cassandra_phase2_core3.trace.xz', 'cass_p2_c3'],
    ['cassandra_phase3_core1.trace.xz', 'cass_p3_c1'], ['cassandra_phase3_core3.trace.xz', 'cass_p3_c3'],
    ['cassandra_phase4_core0.trace.xz', 'cass_p4_c0'], ['cassandra_phase4_core2.trace.xz', 'cass_p4_c2'], ['cassandra_phase4_core3.trace.xz', 'cass_p4_c3'],
    ['cassandra_phase5_core0.trace.xz', 'cass_p5_c0'], ['cassandra_phase5_core1.trace.xz', 'cass_p5_c1'], ['cassandra_phase5_core2.trace.xz', 'cass_p5_c2'], ['cassandra_phase5_core3.trace.xz', 'cass_p5_c3'],
    ['nutch_phase0_core0.trace.xz', 'nutch_p0_c0'], ['nutch_phase0_core1.trace.xz', 'nutch_p0_c1'], ['nutch_phase0_core2.trace.xz', 'nutch_p0_c2'], ['nutch_phase0_core3.trace.xz', 'nutch_p0_c3'],
    ['nutch_phase1_core0.trace.xz', 'nutch_p1_c0'], ['nutch_phase1_core2.trace.xz', 'nutch_p1_c2'], ['nutch_phase1_core3.trace.xz', 'nutch_p1_c3'],
    ['nutch_phase3_core0.trace.xz', 'nutch_p3_c0'], ['nutch_phase3_core1.trace.xz', 'nutch_p3_c1'], ['nutch_phase3_core2.trace.xz', 'nutch_p3_c2'], ['nutch_phase3_core3.trace.xz', 'nutch_p3_c3'],
    ['nutch_phase4_core0.trace.xz', 'nutch_p4_c0'], ['nutch_phase4_core1.trace.xz', 'nutch_p4_c1'], ['nutch_phase4_core2.trace.xz', 'nutch_p4_c2'], ['nutch_phase4_core3.trace.xz', 'nutch_p4_c3'],
    ['streaming_phase0_core1.trace.xz', 'stream_p0_c1'], 
    ['streaming_phase1_core0.trace.xz', 'stream_p1_c0'], ['streaming_phase1_core1.trace.xz', 'stream_p1_c1'], ['streaming_phase1_core3.trace.xz', 'stream_p1_c3'], 
    ['streaming_phase2_core0.trace.xz', 'stream_p2_c0'], ['streaming_phase2_core1.trace.xz', 'stream_p2_c1'], ['streaming_phase2_core2.trace.xz', 'stream_p2_c2'], ['streaming_phase2_core3.trace.xz', 'stream_p2_c3'], 
    ['streaming_phase3_core0.trace.xz', 'stream_p3_c0'], ['streaming_phase3_core1.trace.xz', 'stream_p3_c1'], ['streaming_phase3_core3.trace.xz', 'stream_p3_c3'], 
    ['streaming_phase4_core0.trace.xz', 'stream_p4_c0'], ['streaming_phase4_core1.trace.xz', 'stream_p4_c1'], ['streaming_phase4_core3.trace.xz', 'stream_p4_c3'], 
    ['streaming_phase5_core0.trace.xz', 'stream_p5_c0'], ['streaming_phase5_core1.trace.xz', 'stream_p5_c1'],
    ['cloud9_phase5_core2.trace.xz', 'cloud_p5_c2']
]

workloads_qmm_client = [  
    ['compute_fp_1_new.xz', 'client_fp_01'], ['compute_fp_3_new.xz', 'client_fp_03'], ['compute_fp_5_new.xz', 'client_fp_05'], 
    ['compute_fp_6_new.xz', 'client_fp_06'], ['compute_fp_7_new.xz', 'client_fp_07'], ['compute_fp_8_new.xz', 'client_fp_08'],
    ['compute_fp_10_new.xz', 'client_fp_10'], ['compute_fp_11_new.xz', 'client_fp_11'], ['compute_fp_12_new.xz', 'client_fp_12'],
    ['compute_fp_13_new.xz', 'client_fp_13'], ['compute_int_1_new.xz', 'client_int_1'], ['compute_int_2_new.xz', 'client_int_2'], 
    ['compute_int_3_new.xz', 'client_int_3'], ['compute_int_7_new.xz', 'client_int_7'],  ['compute_int_11_new.xz', 'client_int_11'], 
    ['compute_int_12_new.xz', 'client_int_12'], ['compute_int_14_new.xz', 'client_int_14'], ['compute_int_16_new.xz', 'client_int_16'], 
    ['compute_int_19_new.xz', 'client_int_19'], ['compute_int_21_new.xz', 'client_int_21'], ['compute_int_23_new.xz', 'client_int_23'], 
    ['compute_int_27_new.xz', 'client_int_27'], ['compute_int_31_new.xz', 'client_int_31'], ['compute_int_32_new.xz', 'client_int_32'], 
    ['compute_int_34_new.xz', 'client_int_34'], ['compute_int_37_new.xz', 'client_int_37'], ['compute_int_38_new.xz', 'client_int_38'], 
    ['compute_int_44_new.xz', 'client_int_44'], ['compute_int_45_new.xz', 'client_int_45'], ['compute_int_45_new.xz', 'client_int_46'],
]

workloads_qmm_server = [    
    ['srv_0_new.xz', 'srv_0'], ['srv_1_new.xz', 'srv_1'], ['srv_2_new.xz', 'srv_2'], ['srv_3_new.xz', 'srv_3'], ['srv_4_new.xz', 'srv_4'],
    ['srv_5_new.xz', 'srv_5'], ['srv_6_new.xz', 'srv_6'], ['srv_7_new.xz', 'srv_7'], ['srv_8_new.xz', 'srv_8'], ['srv_9_new.xz', 'srv_9'],
    ['srv_10_new.xz', 'srv_10'], ['srv_27_new.xz', 'srv_27'], ['srv_28_new.xz', 'srv_28'], ['srv_29_new.xz', 'srv_29'], ['srv_30_new.xz', 'srv_30'], 
    ['srv_31_new.xz', 'srv_31'], ['srv_33_new.xz', 'srv_33'], ['srv_34_new.xz', 'srv_34'], ['srv_35_new.xz', 'srv_35'], ['srv_36_new.xz', 'srv_36'], 
    ['srv_37_new.xz', 'srv_37'], ['srv_38_new.xz', 'srv_38'], ['srv_39_new.xz', 'srv_39'], ['srv_40_new.xz', 'srv_40'], ['srv_41_new.xz', 'srv_41'],
    ['srv_44_new.xz', 'srv_44'], ['srv_45_new.xz', 'srv_45'], ['srv_46_new.xz', 'srv_46'], ['srv_47_new.xz', 'srv_47'], ['srv_48_new.xz', 'srv_48'],
    ['srv_49_new.xz', 'srv_49'], ['srv_50_new.xz', 'srv_50'], ['srv_51_new.xz', 'srv_51'], ['srv_52_new.xz', 'srv_52'], ['srv_55_new.xz', 'srv_55'], 
    ['srv_56_new.xz', 'srv_56'], ['srv_60_new.xz', 'srv_60'], ['srv_61_new.xz', 'srv_61'], ['srv_62_new.xz', 'srv_62'], ['srv_63_new.xz', 'srv_63'], 
    ['srv_64_new.xz', 'srv_64'], ['srv_65_new.xz', 'srv_65'], ['srv_66_new.xz', 'srv_66'], ['srv_67_new.xz', 'srv_67'], ['srv_68_new.xz', 'srv_68'], 
    ['srv_69_new.xz', 'srv_69'], ['srv_75_new.xz', 'srv_75'], ['srv_76_new.xz', 'srv_76']
] 

workloads_gap = [
    ['gap.cc.twitter-10B.champsimtrace.xz', 'gap_cc_twi_10'],
    ['gap.cc.web-10B.champsimtrace.xz', 'gap_cc_web_10'],
    ['gap.pr.twitter-10B.champsimtrace.xz', 'gap_pr_twi_10'],
    ['gap.pr.web-10B.champsimtrace.xz', 'gap_pr_web_10'],
    ['gap.tc.twitter-10B.champsimtrace.xz', 'gap_tc_twi_10'],
    ['gap.tc.web-10B.champsimtrace.xz', 'gap_tc_web_10']
]

for workload in workloads_spec06:
    workload.append(False)
for workload in workloads_spec17:
    workload.append(False)
for workload in workloads_ligra:
    workload.append(False)
for workload in workloads_parsec:
    workload.append(False)
for workload in workloads_cloudsuite:
    workload.append(True)
for workload in workloads_qmm_client:
    workload.append(False)
for workload in workloads_qmm_server:
    workload.append(False)
for workload in workloads_gap:
    workload.append(False)

workloads_spec = workloads_spec06 + workloads_spec17
workloads_qmm = workloads_qmm_client + workloads_qmm_server
workloads_all = workloads_spec + workloads_ligra + workloads_parsec + workloads_cloudsuite
workloads_qmm_gap = workloads_qmm + workloads_gap

workloads_shuffled_spec06_spec17_par_lig = [['ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_22000M.length_250M.champsimtrace.xz', 'lig_cps_22000', False], ['470.lbm-1274B.champsimtrace.xz', '470_1274', False], ['605.mcf_s-1536B.champsimtrace.xz', '605_1536', False], ['605.mcf_s-1644B.champsimtrace.xz', '605_1644', False], ['605.mcf_s-782B.champsimtrace.xz', '605_782', False], ['429.mcf-184B.champsimtrace.xz', '429_184', False], ['619.lbm_s-3766B.champsimtrace.xz', '619_3766', False], ['605.mcf_s-665B.champsimtrace.xz', '605_665', False], ['654.roms_s-523B.champsimtrace.xz', '654_523', False], ['602.gcc_s-734B.champsimtrace.xz', '602_734', False], ['parsec_2.1.canneal.simlarge.prebuilt.drop_500M.length_250M.champsimtrace.xz', 'par_ca_500', False], ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_35250M.length_250M.champsimtrace.xz', 'lig_pa_35250', False], ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_500M.length_250M.champsimtrace.xz', 'lig_pr_500', False], ['459.GemsFDTD-765B.champsimtrace.xz', '459_765', False], ['483.xalancbmk-127B.champsimtrace.xz', '483_127', False], ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M.champsimtrace.xz', 'lig_cp_750', False], ['621.wrf_s-6673B.champsimtrace.xz', '621_6673', False], ['ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M.champsimtrace.xz', 'lig_cps_750', False], ['654.roms_s-1390B.champsimtrace.xz', '654_1390', False], ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_15500M.length_250M.champsimtrace.xz', 'lig_bs_15500', False], ['ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_cps_5000', False], ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_51000M.length_250M.champsimtrace.xz', 'lig_pr_51000', False], ['462.libquantum-714B.champsimtrace.xz', '462_714', False], ['459.GemsFDTD-1491B.champsimtrace.xz', '459_1491', False], ['ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_26750M.length_250M.champsimtrace.xz', 'lig_bc_26750', False], ['ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_mis_3500', False], ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_15750M.length_250M.champsimtrace.xz', 'lig_cp_15750', False], ['437.leslie3d-149B.champsimtrace.xz', '437_149', False], ['459.GemsFDTD-1418B.champsimtrace.xz', '459_1418', False], ['ligra_BellmanFord.com-lj.ungraph.gcc_6.3.0_O3.drop_24750M.length_250M.champsimtrace.xz', 'lig_bf_24750', False], ['482.sphinx3-417B.champsimtrace.xz', '482_417', False], ['607.cactuBSSN_s-2421B.champsimtrace.xz', '607_2421', False], ['ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_bc_3500', False], ['429.mcf-22B.champsimtrace.xz', '429_22', False], ['ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_18000M.length_250M.champsimtrace.xz', 'lig_bb_18000', False], ['ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_cps_3500', False], ['450.soplex-247B.champsimtrace.xz', '450_247', False], ['628.pop2_s-17B.champsimtrace.xz', '628_17', False], ['ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_17000M.length_250M.champsimtrace.xz', 'lig_mis_17000', False], ['437.leslie3d-134B.champsimtrace.xz', '437_134', False], ['620.omnetpp_s-874B.champsimtrace.xz', '620_874', False], ['603.bwaves_s-2931B.champsimtrace.xz', '603_2931', False], ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_bs_3500', False], ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_cp_3500', False], ['462.libquantum-1343B.champsimtrace.xz', '462_1343', False], ['481.wrf-455B.champsimtrace.xz', '481_455', False], ['605.mcf_s-472B.champsimtrace.xz', '605_472', False], ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_23750M.length_250M.champsimtrace.xz', 'lig_cp_23750', False], ['607.cactuBSSN_s-3477B.champsimtrace.xz', '607_3477', False], ['437.leslie3d-273B.champsimtrace.xz', '437_273', False], ['654.roms_s-1007B.champsimtrace.xz', '654_1007', False], ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_bfs_3500', False], ['481.wrf-1254B.champsimtrace.xz', '481_1254', False], ['ligra_Triangle.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M.champsimtrace.xz', 'lig_tr_750', False], ['619.lbm_s-2676B.champsimtrace.xz', '619_2676', False], ['ligra_Triangle.com-lj.ungraph.gcc_6.3.0_O3.drop_6000M.length_250M.champsimtrace.xz', 'lig_tr_6000', False], ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_21500M.length_250M.champsimtrace.xz', 'lig_bfs_21500', False], ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_24500M.length_250M.champsimtrace.xz', 'lig_pa_24500', False], ['ligra_Components-Shortcut.com-lj.ungraph.gcc_6.3.0_O3.drop_21000M.length_250M.champsimtrace.xz', 'lig_cps_21000', False], ['619.lbm_s-2677B.champsimtrace.xz', '619_2677', False], ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_17000M.length_250M.champsimtrace.xz', 'lig_bfs_17000', False], ['ligra_BellmanFord.com-lj.ungraph.gcc_6.3.0_O3.drop_4000M.length_250M.champsimtrace.xz', 'lig_bf_4000', False], ['627.cam4_s-490B.champsimtrace.xz', '627_490', False], ['649.fotonik3d_s-7084B.champsimtrace.xz', '649_7084', False], ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_22000M.length_250M.champsimtrace.xz', 'lig_bs_22000', False], ['437.leslie3d-271B.champsimtrace.xz', '437_271', False], ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_cp_5000', False], ['433.milc-337B.champsimtrace.xz', '433_337', False], ['ligra_CF.com-lj.ungraph.gcc_6.3.0_O3.drop_184750M.length_250M.champsimtrace.xz', 'lig_cf_184750', False], ['623.xalancbmk_s-10B.champsimtrace.xz', '623_10', False], ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_500M.length_250M.champsimtrace.xz', 'lig_bfs_500', False], ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_1250M.length_250M.champsimtrace.xz', 'lig_pa_1250', False], ['ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_23000M.length_250M.champsimtrace.xz', 'lig_bb_23000', False], ['482.sphinx3-234B.champsimtrace.xz', '482_234', False], ['ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_15500M.length_250M.champsimtrace.xz', 'lig_bc_15500', False], ['482.sphinx3-1100B.champsimtrace.xz', '482_1100', False], ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_15750M.length_250M.champsimtrace.xz', 'lig_bfs_15750', False], ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_17000M.length_250M.champsimtrace.xz', 'lig_bs_17000', False], ['482.sphinx3-1522B.champsimtrace.xz', '482_1522', False], ['ligra_CF.com-lj.ungraph.gcc_6.3.0_O3.drop_154750M.length_250M.champsimtrace.xz', 'lig_cf_154750', False], ['ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_15750M.length_250M.champsimtrace.xz', 'lig_mis_15750', False], ['ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_bc_5000', False], ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_6000M.length_250M.champsimtrace.xz', 'lig_pa_6000', False], ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_52000M.length_250M.champsimtrace.xz', 'lig_pa_52000', False], ['607.cactuBSSN_s-4004B.champsimtrace.xz', '607_4004', False], ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_pa_3500', False], ['436.cactusADM-1804B.champsimtrace.xz', '436_1804', False], ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_22750M.length_250M.champsimtrace.xz', 'lig_cp_22750', False], ['459.GemsFDTD-1211B.champsimtrace.xz', '459_1211', False], ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_18500M.length_250M.champsimtrace.xz', 'lig_pr_18500', False], ['ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_500M.length_250M.champsimtrace.xz', 'lig_bb_500', False], ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_bfs_5000', False], ['ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_500M.length_250M.champsimtrace.xz', 'lig_bc_500', False], ['649.fotonik3d_s-1176B.champsimtrace.xz', '649_1176', False], ['471.omnetpp-188B.champsimtrace.xz', '471_188', False], ['619.lbm_s-4268B.champsimtrace.xz', '619_4268', False], ['ligra_BFS-Bitvector.com-lj.ungraph.gcc_6.3.0_O3.drop_2500M.length_250M.champsimtrace.xz', 'lig_bb_2500', False], ['ligra_CF.com-lj.ungraph.gcc_6.3.0_O3.drop_2500M.length_250M.champsimtrace.xz', 'lig_cf_2500', False], ['620.omnetpp_s-141B.champsimtrace.xz', '620_141', False], ['ligra_BellmanFord.com-lj.ungraph.gcc_6.3.0_O3.drop_33750M.length_250M.champsimtrace.xz', 'lig_bf_33750', False], ['410.bwaves-2097B.champsimtrace.xz', '410_2097', False], ['433.milc-127B.champsimtrace.xz', '433_127', False], ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_17000M.length_250M.champsimtrace.xz', 'lig_pa_17000', False], ['437.leslie3d-265B.champsimtrace.xz', '437_265', False], ['602.gcc_s-2226B.champsimtrace.xz', '602_2226', False], ['654.roms_s-1070B.champsimtrace.xz', '654_1070', False], ['603.bwaves_s-1740B.champsimtrace.xz', '603_1740', False], ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_79500M.length_250M.champsimtrace.xz', 'lig_pr_79500', False], ['450.soplex-92B.champsimtrace.xz', '450_92', False], ['ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_21250M.length_250M.champsimtrace.xz', 'lig_mis_21250', False], ['623.xalancbmk_s-202B.champsimtrace.xz', '623_202', False], ['parsec_2.1.facesim.simlarge.prebuilt.drop_1500M.length_250M.champsimtrace.xz', 'par_fs_1500', False], ['654.roms_s-293B.champsimtrace.xz', '654_293', False], ['ligra_Components.com-lj.ungraph.gcc_6.3.0_O3.drop_18000M.length_250M.champsimtrace.xz', 'lig_cp_18000', False], ['481.wrf-816B.champsimtrace.xz', '481_816', False], ['ligra_BC.com-lj.ungraph.gcc_6.3.0_O3.drop_15750M.length_250M.champsimtrace.xz', 'lig_bc_15750', False], ['602.gcc_s-1850B.champsimtrace.xz', '602_1850', False], ['649.fotonik3d_s-8225B.champsimtrace.xz', '649_8225', False], ['482.sphinx3-1395B.champsimtrace.xz', '482_1395', False], ['429.mcf-51B.champsimtrace.xz', '429_51', False], ['437.leslie3d-232B.champsimtrace.xz', '437_232', False], ['481.wrf-196B.champsimtrace.xz', '481_196', False], ['481.wrf-1281B.champsimtrace.xz', '481_1281', False], ['482.sphinx3-1297B.champsimtrace.xz', '482_1297', False], ['603.bwaves_s-2609B.champsimtrace.xz', '603_2609', False], ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M.champsimtrace.xz', 'lig_bs_750', False], ['621.wrf_s-8065B.champsimtrace.xz', '621_8065', False], ['473.astar-359B.champsimtrace.xz', '473_359', False], ['ligra_BellmanFord.com-lj.ungraph.gcc_6.3.0_O3.drop_5500M.length_250M.champsimtrace.xz', 'lig_bf_5500', False], ['ligra_BFS.com-lj.ungraph.gcc_6.3.0_O3.drop_20250M.length_250M.champsimtrace.xz', 'lig_bfs_20250', False], ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_18750M.length_250M.champsimtrace.xz', 'lig_bs_18750', False], ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_pr_5000', False], ['ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_750M.length_250M.champsimtrace.xz', 'lig_mis_750', False], ['ligra_MIS.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_mis_5000', False], ['605.mcf_s-994B.champsimtrace.xz', '605_994', False], ['654.roms_s-294B.champsimtrace.xz', '654_294', False], ['ligra_BFSCC.com-lj.ungraph.gcc_6.3.0_O3.drop_5000M.length_250M.champsimtrace.xz', 'lig_bs_5000', False], ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_21750M.length_250M.champsimtrace.xz', 'lig_pr_21750', False], ['parsec_2.1.streamcluster.simlarge.prebuilt.drop_4750M.length_250M.champsimtrace.xz', 'par_sc_4750', False], ['ligra_Triangle.com-lj.ungraph.gcc_6.3.0_O3.drop_3500M.length_250M.champsimtrace.xz', 'lig_tr_3500', False], ['ligra_PageRankDelta.com-lj.ungraph.gcc_6.3.0_O3.drop_24000M.length_250M.champsimtrace.xz', 'lig_pa_24000', False], ['410.bwaves-1963B.champsimtrace.xz', '410_1963', False], ['ligra_PageRank.com-lj.ungraph.gcc_6.3.0_O3.drop_60750M.length_250M.champsimtrace.xz', 'lig_pr_60750', False], ['parsec_2.1.facesim.simlarge.prebuilt.drop_21500M.length_250M.champsimtrace.xz', 'par_fs_21500', False], ['605.mcf_s-484B.champsimtrace.xz', '605_484', False], ['605.mcf_s-1554B.champsimtrace.xz', '605_1554', False], ['459.GemsFDTD-1169B.champsimtrace.xz', '459_1169', False], ['649.fotonik3d_s-10881B.champsimtrace.xz', '649_10881', False], ['429.mcf-192B.champsimtrace.xz', '429_192', False]]
workloads_hete_cloudsuite = [['cassandra_phase0_core0.trace.xz', 'cass_p0_c0'], ['cassandra_phase0_core1.trace.xz', 'cass_p0_c1'], ['cassandra_phase0_core2.trace.xz', 'cass_p0_c2'], ['cassandra_phase0_core3.trace.xz', 'cass_p0_c3'], ['cassandra_phase1_core0.trace.xz', 'cass_p1_c0'], ['cassandra_phase1_core1.trace.xz', 'cass_p1_c1'], ['cassandra_phase1_core2.trace.xz', 'cass_p1_c2'], ['cassandra_phase1_core3.trace.xz', 'cass_p1_c3'], ['cassandra_phase2_core1.trace.xz', 'cass_p2_c1'], ['cassandra_phase2_core2.trace.xz', 'cass_p2_c2'], ['cassandra_phase2_core3.trace.xz', 'cass_p2_c3'], ['cassandra_phase2_core2.trace.xz', 'cass_p2_c2'], ['cassandra_phase3_core1.trace.xz', 'cass_p3_c1'], ['cassandra_phase3_core3.trace.xz', 'cass_p3_c3'], ['cassandra_phase3_core1.trace.xz', 'cass_p3_c1'], ['cassandra_phase3_core3.trace.xz', 'cass_p3_c3'], ['cassandra_phase4_core0.trace.xz', 'cass_p4_c0'], ['cassandra_phase4_core2.trace.xz', 'cass_p4_c2'], ['cassandra_phase4_core3.trace.xz', 'cass_p4_c3'], ['cassandra_phase4_core3.trace.xz', 'cass_p4_c3'], ['cassandra_phase5_core0.trace.xz', 'cass_p5_c0'], ['cassandra_phase5_core1.trace.xz', 'cass_p5_c1'], ['cassandra_phase5_core2.trace.xz', 'cass_p5_c2'], ['cassandra_phase5_core3.trace.xz', 'cass_p5_c3'], ['nutch_phase0_core0.trace.xz', 'nutch_p0_c0'], ['nutch_phase0_core1.trace.xz', 'nutch_p0_c1'], ['nutch_phase0_core2.trace.xz', 'nutch_p0_c2'], ['nutch_phase0_core3.trace.xz', 'nutch_p0_c3'], ['nutch_phase1_core0.trace.xz', 'nutch_p1_c0'], ['nutch_phase1_core1.trace.xz', 'nutch_p1_c1'], ['nutch_phase1_core2.trace.xz', 'nutch_p1_c2'], ['nutch_phase1_core3.trace.xz', 'nutch_p1_c3'], ['nutch_phase3_core0.trace.xz', 'nutch_p3_c0'], ['nutch_phase3_core1.trace.xz', 'nutch_p3_c1'], ['nutch_phase3_core2.trace.xz', 'nutch_p3_c2'], ['nutch_phase3_core3.trace.xz', 'nutch_p3_c3'], ['nutch_phase4_core0.trace.xz', 'nutch_p4_c0'], ['nutch_phase4_core1.trace.xz', 'nutch_p4_c1'], ['nutch_phase4_core2.trace.xz', 'nutch_p4_c2'], ['nutch_phase4_core3.trace.xz', 'nutch_p4_c3'], ['streaming_phase1_core0.trace.xz', 'stream_p1_c0'], ['streaming_phase1_core1.trace.xz', 'stream_p1_c1'], ['streaming_phase1_core1.trace.xz', 'stream_p1_c1'], ['streaming_phase1_core3.trace.xz', 'stream_p1_c3'],  ['streaming_phase2_core0.trace.xz', 'stream_p2_c0'], ['streaming_phase2_core1.trace.xz', 'stream_p2_c1'], ['streaming_phase2_core2.trace.xz', 'stream_p2_c2'], ['streaming_phase2_core3.trace.xz', 'stream_p2_c3'], ['streaming_phase3_core0.trace.xz', 'stream_p3_c0'], ['streaming_phase3_core1.trace.xz', 'stream_p3_c1'], ['streaming_phase3_core3.trace.xz', 'stream_p3_c3'], ['streaming_phase3_core3.trace.xz', 'stream_p3_c3'], ['streaming_phase4_core0.trace.xz', 'stream_p4_c0'], ['streaming_phase4_core0.trace.xz', 'stream_p4_c0'], ['streaming_phase4_core1.trace.xz', 'stream_p4_c1'], ['streaming_phase4_core3.trace.xz', 'stream_p4_c3'], ['streaming_phase5_core0.trace.xz', 'stream_p5_c0'], ['streaming_phase5_core1.trace.xz', 'stream_p5_c1'], ['streaming_phase5_core0.trace.xz', 'stream_p5_c0'], ['streaming_phase5_core1.trace.xz', 'stream_p5_c1']]
for workload in workloads_hete_cloudsuite:
    workload.append(True)


workloads_all_2core_heterogeneous = []
for i in range(0, math.floor(len(workloads_shuffled_spec06_spec17_par_lig)/2)):
    workloads_all_2core_heterogeneous.append([workloads_shuffled_spec06_spec17_par_lig[2*i], workloads_shuffled_spec06_spec17_par_lig[2*i+1]])
for i in range(0, math.floor(len(workloads_hete_cloudsuite)/2)):
    workloads_all_2core_heterogeneous.append([workloads_hete_cloudsuite[2*i], workloads_hete_cloudsuite[2*i+1]])


workloads_all_4core_heterogeneous = []
for i in range(0, math.floor(len(workloads_shuffled_spec06_spec17_par_lig)/4)):
    workloads_all_4core_heterogeneous.append([workloads_shuffled_spec06_spec17_par_lig[4*i], workloads_shuffled_spec06_spec17_par_lig[4*i+1], workloads_shuffled_spec06_spec17_par_lig[4*i+2], workloads_shuffled_spec06_spec17_par_lig[4*i+3]])
for i in range(0, math.floor(len(workloads_hete_cloudsuite)/4)):
    workloads_all_4core_heterogeneous.append([workloads_hete_cloudsuite[4*i], workloads_hete_cloudsuite[4*i+1], workloads_hete_cloudsuite[4*i+2], workloads_hete_cloudsuite[4*i+3]])

    
workloads_all_8core_heterogeneous = []
for i in range(0, math.floor(len(workloads_shuffled_spec06_spec17_par_lig)/8)):
    workloads_all_8core_heterogeneous.append([workloads_shuffled_spec06_spec17_par_lig[8*i], workloads_shuffled_spec06_spec17_par_lig[8*i+1], workloads_shuffled_spec06_spec17_par_lig[8*i+2], workloads_shuffled_spec06_spec17_par_lig[8*i+3], workloads_shuffled_spec06_spec17_par_lig[8*i+4], workloads_shuffled_spec06_spec17_par_lig[8*i+5], workloads_shuffled_spec06_spec17_par_lig[8*i+6], workloads_shuffled_spec06_spec17_par_lig[8*i+7]])

for i in range(0, math.floor(len(workloads_hete_cloudsuite)/8)):
    workloads_all_8core_heterogeneous.append([workloads_hete_cloudsuite[8*i], workloads_hete_cloudsuite[8*i+1], workloads_hete_cloudsuite[8*i+2], workloads_hete_cloudsuite[8*i+3], workloads_hete_cloudsuite[8*i+4], workloads_hete_cloudsuite[8*i+5], workloads_hete_cloudsuite[8*i+6], workloads_hete_cloudsuite[8*i+7]])

workloads_fig10 = [
    '410_1963', '436_1804', '437_271', '481_816',
    '602_1850', 
    '621_8065', '628_17', '654_523', 
    'par_sc_4750', 'par_fs_21500', 
    'nutch_p3_c1', 'nutch_p4_c2',

    'lig_pr_500', 'lig_pr_60750',
    'lig_pa_3500', 'lig_pa_52000',
    'lig_bc_3500', 'lig_bc_26750', 
    'lig_bf_4000', 'lig_bf_33750',  
    'lig_cp_3500', 'lig_cp_23750',
    'lig_cps_3500', 'lig_cps_21000',
]

workloads_fig11 = [
    '433_127',
    '436_1804',
    '437_149',
    '450_247',
    '459_1169', '459_1211',
    '462_714', '462_1343', '470_1274',
    '482_417',  
    '481_196', 
    'lig_bb_18000', 
    'lig_bc_26750', 
    'lig_bf_24750', 
    'lig_bfs_17000', 
    'lig_bs_17000',
    'lig_cf_184750', 
    'lig_cp_23750', 
    'lig_cps_22000', 
    'lig_mis_17000', 
    'lig_pr_79500',
    'lig_pa_24000', 
    'lig_tr_3500', 
    'par_ca_500', 
    'par_fs_1500',
    'par_sc_4750', 
    'cass_p0_c0', 
    'cloud_p5_c2', 
    'nutch_p0_c0', 
    'stream_p1_c0',
    '602_734', '602_2226',
    '603_1740', 
    '605_665', '605_1536',
    '607_3477', 
    '619_2676', 
    '620_141',
    '623_10' ,'623_202', 
    '627_490', 
    '628_17', 
    '649_8225', '649_10881', 
    '654_294', '654_523',
    'spec17', 
    'cloud', 
    'all', 
]

workloads_fig12_gap = [
    ['gap_cc_twi_10', 'cc.twi.10'],
    ['gap_cc_web_10', 'cc.web.10'],
    ['gap_pr_twi_10', 'pr.twi.10'],
    ['gap_pr_web_10', 'pr.web.10'],
    ['gap_tc_twi_10', 'tc.twi.10'],
    ['gap_tc_web_10', 'tc.web.10'], 
    ['gap', 'avg_gap']
]

workloads_fig12_qmm = [
    ['srv_9', 'srv.09'],
    ['srv_27', 'srv.27'],
    ['srv_46', 'srv.46'],
    ['srv_40', 'srv.40'],
    ['srv_67', 'srv.67'],
    ['qmm_server', 'avg_srv'],
    ['client_fp_06', 'clt.fp.06'],
    ['client_fp_08', 'clt.fp.08'],
    ['client_int_1', 'clt.int.01'],
    ['client_int_19', 'clt.int.19'],
    ['client_int_31', 'clt.int.31'],
    ['qmm_client', 'avg_clt'],
]

client_begin_idx = workloads_fig12_qmm.index(['client_fp_06', 'clt.fp.06'])

workloads_all_4core_heterogeneous_fig15 = [
    ('mix1', '481_1254-lig_tr_750-619_2676-lig_tr_6000'),
    ('mix2', '459_1211-lig_pr_18500-lig_bb_500-lig_bfs_5000'),
    ('mix3', '603_2609-lig_bs_750-621_8065-473_359'),
    ('mix4', 'lig_pa_24000-410_1963-lig_pr_60750-par_fs_21500'),
    ('mix5', 'cass_p0_c0-cass_p0_c1-cass_p0_c2-cass_p0_c3')
]


workloads_sensitivity = [
    '410_1963', '470_1274', '471_188', '481_1254', '602_2226', '605_484',
    '623_202', '628_17', '649_7084', '654_1070', 'lig_pr_500', 'lig_pr_60750',
    'lig_bf_4000', 'lig_bf_33750', 'par_sc_4750', 'spec', 'ligra', 'parsec',
]


workloads_name_map = {
    '410_1963': 'bwaves-1963',  '410_2097': 'bwaves-2097',  '429_22': 'mcf-22',  '429_51': 'mcf-51',  '429_184': 'mcf-184',  
    '429_192': 'mcf-192',  '433_127': 'milc-127',  '433_337': 'milc-337',  '437_134': 'leslie3d-134',  '437_149': 'leslie3d-149',  
    '437_232': 'leslie3d-232',  '437_265': 'leslie3d-265',  '437_273': 'leslie3d-273',  '450_247': 'soplex-247',  '459_765': 'GemsFDTD-765',  
    '459_1169': 'GemsFDTD-1169',  '459_1418': 'GemsFDTD-1418',  '459_1491': 'GemsFDTD-1491',  '462_714': 'libquantum-714',  
    '462_1343': 'libquantum-1343',  '470_1274': 'lbm-1274',  '471_188': 'omnetpp-188',  '481_196': 'wrf-196',  
    '481_455': 'wrf-455',  '481_816': 'wrf-816',  '481_1281': 'wrf-1281',  '482_234': 'sphinx3-234',  
    '482_417': 'sphinx3-417',  '482_1100': 'sphinx3-1100',  '482_1297': 'sphinx3-1297',  '482_1395': 'sphinx3-1395', 
    '482_1522': 'sphinx3-1522',  '483_127': 'xalancbmk-127',  '436_1804': 'cactusADM-1804',  '437_271': 'leslie3d-271',  
    '450_92': 'soplex-92',  '459_1211': 'GemsFDTD-1211',  '473_359': 'astar-359',  '481_1254': 'wrf-1254',  
    '602_734': 'gcc_s-734',  '602_1850': 'gcc_s-1850',  '602_2226': 'gcc_s-2226',  '603_1740': 'bwaves_s-1740',  
    '603_2609': 'bwaves_s-2609',  '603_2931': 'bwaves_s-2931',  '605_484': 'mcf_s-484',  '605_665': 'mcf_s-665',  
    '605_782': 'mcf_s-782',  '605_472': 'mcf_s-472',  '605_994': 'mcf_s-994',  '605_1536': 'mcf_s-1536',  
    '605_1554': 'mcf_s-1554',  '605_1644': 'mcf_s-1644',  '607_2421': 'cactuBSSN_s-2421',  '607_3477': 'cactuBSSN_s-3477',  
    '607_4004': 'cactuBSSN_s-4004',  '619_2676': 'lbm_s-2676',  '619_2677': 'lbm_s-2677',  '619_3766': 'lbm_s-3766',  
    '619_4268': 'lbm_s-4268',  '620_141': 'omnetpp_s-141',  '620_874': 'omnetpp_s-874',  '621_6673': 'wrf_s-6673',  
    '621_8065': 'wrf_s-8065',  '623_10': 'xalancbmk_s-10',  '623_202': 'xalancbmk_s-202',  '627_490': 'cam4_s-490',  
    '628_17': 'pop2_s-17',  '649_1176': 'fotonik3d_s-1176',  '649_7084': 'fotonik3d_s-7084',  
    '649_8225': 'fotonik3d_s-8225',  '649_10881': 'fotonik3d_s-10881',  '654_293': 'roms_s-293',  '654_294': 'roms_s-294',  
    '654_523': 'roms_s-523',  '654_1007': 'roms_s-1007',  '654_1070': 'roms_s-1070',  '654_1390': 'roms_s-1390',  
    'lig_pr_51000': 'PageRank-51',  'lig_pr_79500': 'PageRank-80',  'lig_pr_18500': 'PageRank-19',  
    'lig_pr_21750': 'PageRank-22',  'lig_pr_5000': 'PageRank-5',  'lig_pr_500': 'PageRank-1',  
    'lig_pr_60750': 'PageRank-61',  'lig_pa_1250': 'PageRank.D-1',  'lig_pa_3500': 'PageRank.D-3',  
    'lig_pa_6000': 'PageRank.D-6',  'lig_pa_17000': 'PageRank.D-17',  'lig_pa_24000': 'PageRank.D-24',  
    'lig_pa_24500': 'PageRank.D-25',  'lig_pa_35250': 'PageRank.D-35',  'lig_pa_52000': 'PageRank.D-52',  
    'lig_tr_750': 'Triangle-1',  'lig_tr_3500': 'Triangle-4',  'lig_tr_6000': 'Triangle-6',  'lig_bc_26750': 
    'BC-27',  'lig_bc_15750': 'BC-16',  'lig_bc_15500': 'BC-15',  'lig_bc_5000': 'BC-5',  'lig_bc_3500': 'BC-4',  
    'lig_bc_500': 'BC-1',  'lig_bf_4000': 'BellmanFord-4',  'lig_bf_5500': 'BellmanFord-6',  
    'lig_bf_24750': 'BellmanFord-25',  'lig_bf_33750': 'BellmanFord-34',  'lig_bb_18000': 'BFS.B-18',  
    'lig_bb_23000': 'BFS.B-23',  'lig_bb_2500': 'BFS.B-3',  'lig_bb_500': 'BFS.B-5',  'lig_bs_15500': 'BFSCC-16',  
    'lig_bs_17000': 'BFSCC-17',  'lig_bs_18750': 'BFSCC-19',  'lig_bs_22000': 'BFSCC-22',  'lig_bs_3500': 'BFSCC-4',  
    'lig_bs_5000': 'BFSCC-5',  'lig_bs_750': 'BFSCC-1',  'lig_bfs_15750': 'BFS-16',  'lig_bfs_17000': 'BFS-17',  
    'lig_bfs_20250': 'BFS-20',  'lig_bfs_21500': 'BFS-22',  'lig_bfs_3500': 'BFS-4',  'lig_bfs_5000': 'BFS-5',  
    'lig_bfs_500': 'BFS-1',  'lig_cf_154750': 'CF-155',  'lig_cf_184750': 'CF-185',  'lig_cf_2500': 'CF-3',  
    'lig_cp_15750': 'Components-16',  'lig_cp_18000': 'Components-18',  'lig_cp_22750': 'Components-23',  
    'lig_cp_23750': 'Components-24',  'lig_cp_3500': 'Components-4',  'lig_cp_5000': 'Components-5',  
    'lig_cp_750': 'Components-1',  'lig_cps_21000': 'Components.S-21',  'lig_cps_22000': 'Components.S-22',  
    'lig_cps_3500': 'Components.S-4',  'lig_cps_5000': 'Components.S-5',  'lig_cps_750': 'Components.S-1',  
    'lig_mis_15750': 'MIS-16',  'lig_mis_17000': 'MIS-17',  'lig_mis_21250': 'MIS-22',  'lig_mis_3500': 'MIS-4',  
    'lig_mis_5000': 'MIS-5',  'lig_mis_750': 'MIS-1',  'par_ca_500': 'canneal-1',  'par_fs_1500': 'facesim-2',  
    'par_fs_21500': 'facesim-22',  'par_sc_4750': 'streamcluster-5',  'cass_p0_c0': 'cassandra-p0c0',  
    'cass_p0_c1': 'cassandra-p0c1',  'cass_p0_c2': 'cassandra-p0c2',  'cass_p0_c3': 'cassandra-p0c3',  
    'cass_p1_c0': 'cassandra-p1c0',  'cass_p1_c1': 'cassandra-p1c1',  'cass_p1_c2': 'cassandra-p1c2',  
    'cass_p1_c3': 'cassandra-p1c3',  'cass_p2_c1': 'cassandra-p2c1',  'cass_p2_c2': 'cassandra-p2c2',  
    'cass_p2_c3': 'cassandra-p2c3',  'cass_p3_c1': 'cassandra-p3c1',  'cass_p3_c3': 'cassandra-p3c3',  
    'cass_p4_c0': 'cassandra-p4c0',  'cass_p4_c2': 'cassandra-p4c2',  'cass_p4_c3': 'cassandra-p4c3',  
    'cass_p5_c0': 'cassandra-p5c0',  'cass_p5_c1': 'cassandra-p5c1',  'cass_p5_c2': 'cassandra-p5c2',  
    'cass_p5_c3': 'cassandra-p5c3',  'nutch_p0_c0': 'nutch-p0c0',  'nutch_p0_c1': 'nutch-p0c1',  
    'nutch_p0_c2': 'nutch-p0c2',  'nutch_p0_c3': 'nutch-p0c3',  'nutch_p1_c0': 'nutch-p1c0',  'nutch_p1_c2': 'nutch-p1c2',  
    'nutch_p1_c3': 'nutch-p1c3',  'nutch_p3_c0': 'nutch-p3c0',  'nutch_p3_c1': 'nutch-p3c1',  'nutch_p3_c2': 'nutch-p3c2',  
    'nutch_p3_c3': 'nutch-p3c3',  'nutch_p4_c0': 'nutch-p4c0',  'nutch_p4_c1': 'nutch-p4c1',  'nutch_p4_c2': 'nutch-p4c2',  
    'nutch_p4_c3': 'nutch-p4c3',  'stream_p0_c1': 'stream-p0c1',  'stream_p1_c0': 'stream-p1c0',  
    'stream_p1_c1': 'stream-p1c1',  'stream_p1_c3': 'stream-p1c3',  'stream_p2_c0': 'stream-p2c0',  
    'stream_p2_c1': 'stream-p2c1',  'stream_p2_c2': 'stream-p2c2',  'stream_p2_c3': 'stream-p2c3',  
    'stream_p3_c0': 'stream-p3c0',  'stream_p3_c1': 'stream-p3c1',  'stream_p3_c3': 'stream-p3c3',  
    'stream_p4_c0': 'stream-p4c0',  'stream_p4_c1': 'stream-p4c1',  'stream_p4_c3': 'stream-p4c3',  
    'stream_p5_c0': 'stream-p5c0',  'stream_p5_c1': 'stream-p5c1',  'cloud_p5_c2': 'cloud9-p5c2',
    'gap_cc_twi_10': 'cc.twi-10', 'gap_cc_web_10': 'cc.web-10', 'gap_pr_twi_10': 'pr.twi-10',
    'gap_pr_web_10': 'pr.web-10', 'gap_tc_twi_10': 'tc.twi-10', 'gap_tc_web_10': 'tc.web-10',
    'client_fp_01': 'clt.fp.01',  'client_fp_03': 'clt.fp.03',  'client_fp_05': 'clt.fp.05',  'client_fp_06': 'clt.fp.06',  
    'client_fp_07': 'clt.fp.07',  'client_fp_08': 'clt.fp.08',  'client_fp_10': 'clt.fp.10',  'client_fp_11': 'clt.fp.11',  
    'client_fp_12': 'clt.fp.12',  'client_fp_13': 'clt.fp.13',  'client_int_1': 'clt.int.01',  'client_int_2': 'clt.int.02',  
    'client_int_3': 'clt.int.03',  'client_int_7': 'clt.int.07',  'client_int_11': 'clt.int.11',  
    'client_int_12': 'clt.int.12',  'client_int_14': 'clt.int.14',  'client_int_16': 'clt.int.16',  
    'client_int_19': 'clt.int.19',  'client_int_21': 'clt.int.21',  'client_int_23': 'clt.int.23',  
    'client_int_27': 'clt.int.27',  'client_int_31': 'clt.int.31',  'client_int_32': 'clt.int.32',  
    'client_int_34': 'clt.int.34',  'client_int_37': 'clt.int.37',  'client_int_38': 'clt.int.38',  
    'client_int_44': 'clt.int.44',  'client_int_45': 'clt.int.45',  'client_int_46': 'clt.int.45',  
    'client_int_41': 'clt.int.41',  'client_int_42': 'clt.int.42',  'client_int_43': 'clt.int.43',  
    'srv_0': 'srv.00',  'srv_1': 'srv.01',  'srv_2': 'srv.02',  'srv_3': 'srv.03',  'srv_4': 'srv.04',  
    'srv_5': 'srv.05',  'srv_6': 'srv.06',  'srv_7': 'srv.07',  'srv_8': 'srv.08',  'srv_9': 'srv.09',  
    'srv_10': 'srv.10',  'srv_27': 'srv.27',  'srv_28': 'srv.28',  'srv_29': 'srv.29',  'srv_30': 'srv.30',  
    'srv_31': 'srv.31',  'srv_33': 'srv.33',  'srv_34': 'srv.34',  'srv_35': 'srv.35',  'srv_36': 'srv.36',  
    'srv_37': 'srv.37',  'srv_38': 'srv.38',  'srv_39': 'srv.39',  'srv_40': 'srv.40',  'srv_41': 'srv.41',  
    'srv_44': 'srv.44',  'srv_45': 'srv.45',  'srv_46': 'srv.46',  'srv_47': 'srv.47',  'srv_48': 'srv.48',  
    'srv_49': 'srv.49',  'srv_50': 'srv.50',  'srv_51': 'srv.51',  'srv_52': 'srv.52',  'srv_55': 'srv.55',  
    'srv_56': 'srv.56',  'srv_60': 'srv.60',  'srv_61': 'srv.61',  'srv_62': 'srv.62',  'srv_63': 'srv.63',  
    'srv_64': 'srv.64',  'srv_65': 'srv.65',  'srv_66': 'srv.66',  'srv_67': 'srv.67',  'srv_68': 'srv.68',  
    'srv_69': 'srv.69',  'srv_75': 'srv.75',  'srv_76': 'srv.76',
}