// ULA 6C001 VII
// Higher-level processing of the "decompiled" netlist. Using the annotated schematic we spread the netlist "sheet" over modules and the design becomes more modular.
// Also RS-FFs from two looped nor are "tucked away" into higher-level primitives (`GD`, `FD`, etc.) so that we can use synchronous design for sequential elements.
// The entire combo (nor-trees) remain as in the original, but are defined explicitly via intrinsics `not`, `nor` instead of modules so that EDA draws nice gate symbols. There's no point in cleaning up the combo, except for the fact that it's only possible to demorganize it when it's too boring.

module ula (  n_INT, A6, A5, A4, A3, A2, A1, A0, n_WE, n_RD, n_WR, n_CAS, OSC, n_MREQ, A15, A14, n_RAS, n_ROMCS, n_IOREQ, n_PHICPU, D7, D6, D5, D4, SOUND, KB4, D3, D2, D1, D0, KB0, KB1, KB2, KB3, n_Y, V, U);

	output wire n_INT;
	output wire A6;
	output wire A5;
	output wire A4;
	output wire A3;
	output wire A2;
	output wire A1;
	inout wire A0;
	output wire n_WE;
	input wire n_RD;
	input wire n_WR;
	output wire n_CAS;
	input wire OSC;
	input wire n_MREQ;
	input wire A15;
	input wire A14;
	output wire n_RAS;
	output wire n_ROMCS;
	input wire n_IOREQ;
	output wire n_PHICPU;
	inout wire D7;
	inout wire D6;
	input wire D5;
	inout wire D4;
	inout wire SOUND;
	input wire KB4;
	inout wire D3;
	inout wire D2;
	inout wire D1;
	inout wire D0;
	inout wire KB0;
	input wire KB1;
	input wire KB2;
	input wire KB3;
	output wire n_Y;
	output wire V;
	output wire U;

	// Wires

	wire BlueD; 				// Blue`
	wire RedD; 			// Red`
	wire w3;
	wire w4;
	wire w5;
	wire w6;
	wire w7;
	wire w8;
	wire w9;
	wire w10;
	wire w11;
	wire w13;
	wire w14;
	wire w15;
	wire w16;
	wire w17;
	wire w18;
	wire w19;
	wire w20;
	wire w21;
	wire w22;
	wire w23;
	wire w24;
	wire w25;
	wire w26;
	wire w27;
	wire w28;
	wire w29;
	wire w30;
	wire w31;
	wire w32;
	wire w33;
	wire w34;
	wire w35;
	wire w36;
	wire w37;
	wire w38;
	wire w39;
	wire w40;
	wire w41;
	wire w42;
	wire w43;
	wire w45;
	wire w46;
	wire w47;
	wire w48;
	wire w49;
	wire w50;
	wire w51;
	wire w52;
	wire w53;
	wire w54;
	wire w55;
	wire w56;
	wire w57;
	wire w58;
	wire w59;
	wire w60;
	wire w61;
	wire w62;
	wire w63;
	wire w64;
	wire w65;
	wire w66;
	wire w67;
	wire w68;
	wire w69;
	wire w70;
	wire w71;
	wire w72;
	wire w73;
	wire w74;
	wire w75;
	wire w76;
	wire w77;
	wire w78;
	wire w79;
	wire w80;
	wire w81;
	wire w82;
	wire w83;
	wire w84;
	wire w85;
	wire w86;
	wire w87;
	wire w88;
	wire w89;
	wire w90;
	wire w91;
	wire w92;
	wire w93;
	wire w94;
	wire w95;
	wire w96;
	wire w97;
	wire w98;
	wire w99;
	wire w101;
	wire w102;
	wire w103;
	wire w104;
	wire w106;
	wire w107;
	wire w109;
	wire w110;
	wire w112;
	wire w113;
	wire w115;
	wire w116;
	wire w117;
	wire w118;
	wire w119;
	wire w120;
	wire w121;
	wire w123;
	wire w124;
	wire w126;
	wire w127;
	wire w129;
	wire w130;
	wire nRedDD; 			// /Red``
	wire w132;
	wire w133;
	wire w134;
	wire w135;
	wire w136;
	wire w137;
	wire w139;
	wire w140;
	wire w141;
	wire w143;
	wire w144;
	wire w145;
	wire w146;
	wire w147;
	wire w148;
	wire w149;
	wire w150;
	wire w151;
	wire w153;
	wire w154;
	wire w156;
	wire w160;
	wire w161;
	wire w162;
	wire w163;
	wire w164;
	wire w165;
	wire w166;
	wire w167;
	wire w168;
	wire w169;
	wire w171;
	wire w172;
	wire w173;
	wire w174;
	wire w175;
	wire w176;
	wire w177;
	wire w178;
	wire w179;
	wire w180;
	wire w181;
	wire w182;
	wire w183;
	wire w184;
	wire w185;
	wire w186;
	wire w187;
	wire w188;
	wire w189;
	wire w190;
	wire w191;
	wire w192;
	wire w193;
	wire w196;
	wire w197;
	wire w199;
	wire w200;
	wire w201;
	wire w202;
	wire w203;
	wire w204;
	wire w205;
	wire w206;
	wire w207;
	wire w208;
	wire w209;
	wire w210;
	wire w211;
	wire w212;
	wire w216;
	wire w217;
	wire w219;
	wire w220;
	wire w221;
	wire w223;
	wire w224;
	wire w225;
	wire w226;
	wire w227;
	wire w228;
	wire w229;
	wire w230;
	wire w231;
	wire w232;
	wire w233;
	wire w234;
	wire w235;
	wire w237;
	wire w238;
	wire w239;
	wire w240;
	wire w241;
	wire w242;
	wire w243;
	wire w244;
	wire w245;
	wire w246;
	wire w247;
	wire w248;
	wire w249;
	wire w250;
	wire w251;
	wire w253;
	wire w258;
	wire nIOREQ_from_pad; 		// w259
	wire w260;
	wire w261;
	wire w263;
	wire w264;
	wire w265;
	wire w266;
	wire w267;
	wire w268;
	wire w269;
	wire w270;
	wire w272;
	wire w273;
	wire w274;
	wire w275;
	wire w276;
	wire w277;
	wire w278;
	wire w279;
	wire w280;
	wire w281;
	wire w282;
	wire w283;
	wire w284;
	wire w285;
	wire w286;
	wire w287;
	wire w288;
	wire w289;
	wire w290;
	wire w291;
	wire w292;
	wire w293;
	wire w294;
	wire w295;
	wire w296;
	wire w297;
	wire w298;
	wire w300;
	wire w302;
	wire w303;
	wire w304;
	wire w305;
	wire w307;
	wire w308;
	wire w309;
	wire w310;
	wire w311;
	wire w312;
	wire nMREQ_from_pad; 		//  w314
	wire w315;
	wire w316;
	wire w317;
	wire w318;
	wire w320;
	wire w322;
	wire w323;
	wire w326;
	wire w327;
	wire w328;
	wire w330;
	wire w331;
	wire w333;
	wire w334;
	wire w335;
	wire w336;
	wire w337;
	wire w338;
	wire w339;
	wire w340;
	wire w342;
	wire w343;
	wire Border; 		// w348
	wire w349;
	wire w350;
	wire w351;
	wire w352;
	wire w353;
	wire w354;
	wire w355;
	wire w357;
	wire A15_from_pad; 		// w358
	wire w362;
	wire w363;
	wire w364;
	wire w365;
	wire w366;
	wire w367;
	wire w368;
	wire w369;
	wire w371;
	wire w372;
	wire w373;
	wire w374;
	wire w375;
	wire w376;
	wire w377;
	wire w378;
	wire w379;
	wire nCLK7;
	wire w381;
	wire w382;
	wire w383;
	wire w384;
	wire w385;
	wire w386;
	wire w388;
	wire w389;
	wire w391;
	wire w393;
	wire w394;
	wire w395;
	wire w396;
	wire w398;
	wire w399;
	wire w400;
	wire w401;
	wire w402;
	wire w403;
	wire w406;
	wire A14_from_pad; 		// w407
	wire w408;
	wire w409;
	wire w410;
	wire w412;
	wire w413;
	wire CPUCLK;
	wire w416;
	wire w417;
	wire w418;
	wire w419;
	wire w420;
	wire w421;
	wire w422;
	wire w423;
	wire w424;
	wire w427;
	wire w428;
	wire w429;
	wire w430;
	wire w431;
	wire w432;
	wire w433;
	wire w434;
	wire w435;
	wire w436;
	wire w437;
	wire w438;
	wire w439;
	wire osc_from_pad;
	wire w447;
	wire w450;
	wire w451;
	wire w452;
	wire w453;
	wire w455;
	wire w457;
	wire w458;
	wire w459;
	wire w460;
	wire w461;
	wire w462;
	wire w465;
	wire w468;
	wire w469;
	wire w471;
	wire w472;
	wire w474;
	wire w476;
	wire w478;
	wire w479;
	wire w480;
	wire w481;
	wire w483;
	wire w485;
	wire nTape; 		// w486
	wire w489;
	wire w491;
	wire w492;
	wire w493;
	wire w494;
	wire w495;
	wire w496;
	wire w498;
	wire w499;
	wire w500;
	wire w501;
	wire w503;
	wire w504;
	wire w506;
	wire w507;
	wire w509;
	wire w510;
	wire w511;
	wire w512;
	wire w513;
	wire w515;
	wire w516;
	wire w517;
	wire w519;
	wire w520;
	wire w521;
	wire w522;
	wire w524;
	wire w527;
	wire w528;
	wire w529;
	wire w532;
	wire w534;
	wire w536;
	wire w537;
	wire w538;
	wire w539;
	wire w540;
	wire w541;
	wire w542;
	wire w546;
	wire w547;
	wire w549;
	wire w550;
	wire w551;
	wire w554;
	wire w556;
	wire w558;
	wire w564;
	wire w565;
	wire w566;
	wire w567;
	wire w568;
	wire w569;
	wire w570;
	wire w572;
	wire w573;
	wire w574;
	wire w575;
	wire w576;
	wire w577;
	wire w578;
	wire w579;
	wire w581;
	wire w582;
	wire w583;
	wire w584;
	wire w585;
	wire w587;
	wire w588;
	wire w589;
	wire w590;
	wire w592;
	wire w593;
	wire w594;
	wire w596;
	wire w597;
	wire w599;
	wire w606;
	wire w607;
	wire w608;
	wire w610;
	wire w613;
	wire w615;
	wire w617;
	wire w619;
	wire w620;
	wire w622;
	wire w623;
	wire w624;
	wire w627;
	wire w629;
	wire w630;
	wire w631;
	wire w632;
	wire w638;
	wire w639;
	wire w640;
	wire w642;
	wire w643;
	wire w644;
	wire w645;
	wire w647;
	wire w650;
	wire w655;
	wire w656;
	wire w657;
	wire w658;
	wire w661;
	wire w662;
	wire w663;
	wire w664;
	wire w665;
	wire w666;
	wire nAE;
	wire w668;
	wire w669;
	wire w670;
	wire w671;
	wire w672;
	wire w673;
	wire w674;
	wire w675;
	wire w680;
	wire w681;
	wire w684;
	wire w685;
	wire w687;

	assign n_INT = w668;
	assign A6 = w669;
	assign A5 = w670;
	assign A4 = w671;
	assign A3 = w672;
	assign A2 = w673;
	assign A1 = w674;
	assign A0 = w675;
	assign n_WE = w666;
	assign w665 = n_RD;
	assign w664 = n_WR;
	assign n_CAS = w663;
	assign w662 = OSC;
	assign w661 = n_MREQ;
	assign n_RAS = w658;
	assign n_ROMCS = w657;
	assign w656 = n_IOREQ;
	assign n_PHICPU = w655;
	assign w687 = KB4;
	assign KB0 = w680;
	assign w681 = KB1;
	assign w684 = KB2;
	assign w685 = KB3;

	// Instances

	clkgen clkgen_inst (
		.osc_from_pad(osc_from_pad), 
		.nCLK7(nCLK7) );

	hcounter hcounter_inst ();

	vcounter vcounter_inst ();

	tclk tclk_inst ();

	latch_control latch_control_inst ();

	data_latch data_latch_inst ();

	attr_latch attr_latch_inst ();

	ao_latch ao_latch_inst ();

	pixel_shift_reg pixel_shift_reg_inst ();

	flash_clock flash_clock_inst ();

	flash_xnor flash_xnor_inst ();

	color_mux color_mux_inst ();

	video_addr_gen video_addr_gen_inst ();

	address_enable address_enable_inst ();

	ras_cas_romcs ras_cas_romcs_inst ();

	video_signal_features video_signal_features_inst ();

	dac_setup dac_setup_inst ();

	io io_inst ();

	contention contention_inst ();

	// Pads

	ula_pad_data_bidir g651 (.pad(D0), .from_pad(w7), .to_pad(w10) ); 		// 0
	ula_pad_data_bidir g648 (.pad(D1), .from_pad(w478), .to_pad(w6) );	 	// 1
	ula_pad_data_bidir g647 (.pad(D2), .from_pad(w512), .to_pad(w644) );		// 2
	ula_pad_data_bidir g644 (.pad(D3), .from_pad(w608), .to_pad(w582) ); 		// 3
	ula_pad_data_bidir g642 (.pad(D4), .from_pad(w522), .to_pad(w536) );		// 4
	ula_pad_data_input g640 (.pad(D5), .from_pad(w416) ); 					// 5  - Read only
	ula_pad_data_bidir g639 (.pad(D6), .to_pad(w515), .from_pad(w516) ); 		// 6
	ula_pad_data_bidir g638 (.pad(D7), .from_pad(w417) ); 					// 7  - Read only

	ula_pad_we_output g626 (.pad(w666), .to_pad(w316) );
	ula_pad_rd_input g627 (.pad(w665), .from_pad(w309) );
	ula_pad_wr_input g628 (.pad(w664), .from_pad(w244) );
	ula_pad_cas_output g629 (.pad(w663), .to_pad(w421) );
	ula_pad_osc g630 (.pad(w662), .from_pad(osc_from_pad) );
	ula_pad_mreq_input g631 (.pad(w661), .from_pad(nMREQ_from_pad) );
	ula_pad_addr_input g632 (.pad(A15), .from_pad(A15_from_pad) );
	ula_pad_addr_input g633 (.pad(A14), .from_pad(A14_from_pad) );
	ula_pad_ras_output g634 (.pad(w658), .n_oe(w438), .to_pad(w439) );
	ula_pad_romcs_output g635 (.pad(w657), .to_pad(w409) );
	ula_pad_ioreq_input g636 (.pad(w656), .from_pad(nIOREQ_from_pad) );
	ula_pad_phi_output g637 (.pad(w655), .to_pad(CPUCLK) );
	ula_SoundDAC g641 (.pad(SOUND), .from_pad(w513), .to_pad1(nTape), .to_pad2(w485) );
	ula_pad_kb_input g643 (.pad(w687), .from_pad(w647) );
	ula_pad_kb_input g645 (.pad(w685), .from_pad(w581) );
	ula_pad_kb_input g646 (.pad(w684), .from_pad(w645) );
	ula_pad_kb_input g649 (.pad(w681), .from_pad(w9) );
	ula_pad_kb_bidir g650 (.pad(w680), .from_pad(w13), .to_pad(w276) );
	ula_VideoDAC g652 (.u(U), .v(V), .ny(n_Y), .i14(w4), .i13(w5), .i12(w124), .i11(RedD), .i10(w154), .i9(BlueD), .i8(w144), .i7(w136), .i6(w132), .i5(w137), .i4(w145), .i3(w146), .i2(nRedDD), .i1(w147), .i0(w58) );
	ula_pad_addr_bidir g653 (.pad(w675), .n_oe(nAE), .from_pad(w310), .to_pad(w173) );
	ula_pad_addr_output g654 (.pad(w674), .n_oe(nAE), .to_pad(w191) );
	ula_pad_addr_output g655 (.pad(w673), .n_oe(nAE), .to_pad(w327) );
	ula_pad_addr_output g656 (.pad(w672), .n_oe(nAE), .to_pad(w323) );
	ula_pad_addr_output g657 (.pad(w671), .n_oe(nAE), .to_pad(w322) );
	ula_pad_addr_output g658 (.pad(w670), .n_oe(nAE), .to_pad(w274) );
	ula_pad_addr_output g659 (.pad(w669), .n_oe(nAE), .to_pad(w275) );
	ula_pad_int_output g660 (.pad(w668), .to_pad(w117) );
endmodule // ula


module clkgen (input wire osc_from_pad, output wire nCLK7);
	wire w441;
	wire w442;
	wire w443;
	wire w444;
	wire w445;
	wire w446;
	wire w449;

	ula_not g52 (.a(osc_from_pad), .x(w441) );
	// FD
	ula_nor g423 (.a(w442), .b(w449), .x(w443) );
	ula_nor g424 (.a(w444), .b(w442), .x(w446) );
	ula_nor g425 (.a(w443), .b(w441), .x(w442) );
	ula_nor g430 (.a(w441), .b(w442), .x(w445) );
	ula_nor g431 (.a(w446), .b(w445), .x(w444) );
	ula_nor g432 (.a(w444), .b(w445), .x(w449) );

	ula_not g54 (.a(w446), .x(nCLK7) );	
endmodule // clkgen

module hcounter (input wire nCLK7);
	wire w122;
	wire w157;
	wire w222;	
	wire w329;
	wire w332;

	ula_not g61 (.a(nCLK7), .x(w337) );
	// 0
	ula_nor g444 (.a(w334), .b(w335), .x(w476) );
	ula_nor g445 (.a(w337), .b(w476), .x(w334) );
	ula_nor g446 (.a(w337), .b(w334), .x(w333) );
	ula_nor g453 (.a(w338), .b(w333), .x(w336) );
	ula_nor g454 (.a(w334), .b(w336), .x(w338) );
	ula_nor g455 (.a(w336), .b(w333), .x(w335) );

	ula_nor g447 (.a(nCLK7), .b(w336), .x(w383) );
	// 1	
	ula_nor g470 (.a(w383), .b(w384), .x(w385) );
	ula_nor g471 (.a(w385), .b(w383), .x(w332) );
	ula_nor g472 (.a(w385), .b(w331), .x(w72) );
	ula_nor g468 (.a(w332), .b(w331), .x(w386) );
	ula_nor g469 (.a(w386), .b(w385), .x(w384) );
	ula_nor g452 (.a(w72), .b(w332), .x(w331) );

	ula_nor3 g478 (.a(w336), .b(nCLK7), .c(w331), .x(w232) );
	// 2
	ula_nor g496 (.a(w233), .b(w234), .x(w209) );
	ula_nor g497 (.a(w209), .b(w231), .x(w230) );
	ula_nor g498 (.a(w232), .b(w230), .x(w231) );
	ula_nor g499 (.a(w231), .b(w232), .x(w233) );
	ula_nor g524 (.a(w231), .b(w234), .x(w208) );
	ula_nor g507 (.a(w208), .b(w233), .x(w234) );

	ula_nor4 g479 (.a(w234), .b(nCLK7), .c(w336), .d(w331), .x(w207) );
	// 3
	ula_nor g492 (.a(w204), .b(w203), .x(w329) );
	ula_nor g493 (.a(w329), .b(w205), .x(w206) );
	ula_nor g494 (.a(w207), .b(w206), .x(w205) );
	ula_nor g495 (.a(w205), .b(w207), .x(w204) );
	ula_nor g508 (.a(w204), .b(w253), .x(w203) );
	ula_nor g509 (.a(w205), .b(w203), .x(w253) );

	ula_not g78 (.a(w203), .x(w224) );
	// 4
	ula_nor g510 (.a(w222), .b(w227), .x(w226) );
	ula_nor g511 (.a(w223), .b(w226), .x(w225) );
	ula_nor g512 (.a(w224), .b(w225), .x(w223) );
	ula_nor g513 (.a(w223), .b(w224), .x(w222) );
	ula_nor g521 (.a(w227), .b(w223), .x(w113) );
	ula_nor g522 (.a(w222), .b(w113), .x(w227) );

	ula_nor g491 (.a(w227), .b(w203), .x(w202) );
	// 5
	ula_nor g514 (.a(w220), .b(w229), .x(w200) );
	ula_nor g515 (.a(w201), .b(w221), .x(w220) );
	ula_nor g489 (.a(w202), .b(w229), .x(w201) );
	ula_nor g490 (.a(w200), .b(w202), .x(w229) );
	ula_nor g519 (.a(w221), .b(w229), .x(w112) );
	ula_nor g520 (.a(w201), .b(w112), .x(w221) );

	ula_nor g518 (.a(w228), .b(w221), .x(w34) );
	// 6
	ula_nor g98 (.a(w27), .b(w34), .x(w148) );
	ula_nor g99 (.a(w34), .b(w148), .x(w28) );
	ula_nor3 g100 (.b(w81), .a(w28), .c(w17), .x(w26) );
	ula_nor g101 (.a(w26), .b(w148), .x(w27) );
	ula_nor g102 (.a(w148), .b(w17), .x(w70) );
	ula_nor g103 (.b(w28), .a(w70), .x(w17) );

	// 7
	ula_nor g111 (.a(w70), .b(w79), .x(w122) );
	ula_nor g112 (.a(w79), .b(w85), .x(w16) );
	ula_nor g113 (.a(w84), .b(w16), .x(w79) );
	ula_nor g114 (.a(w17), .b(w16), .x(w80) );
	ula_nor g115 (.a(w79), .b(w70), .x(w157) );
	ula_nor4 g116 (.a(w157), .b(w85), .c(w81), .x(w83), .d(w80) );
	ula_nor g121 (.a(w84), .b(w83), .x(w82) );
	ula_nor g122 (.a(w82), .b(w34), .x(w84) );
	ula_nor g123 (.a(w34), .b(w84), .x(w85) );

	// 8
	ula_nor g108 (.a(w31), .b(w122), .x(w77) );
	ula_nor g109 (.a(w78), .b(w120), .x(w121) );
	ula_not g110 (.a(w122), .x(w120) );
	ula_nor g124 (.a(w73), .b(w75), .x(w74) );
	ula_nor g125 (.a(w74), .b(w34), .x(w75) );
	ula_nor g126 (.a(w34), .b(w75), .x(w76) );
	ula_nor4 g127 (.a(w81), .b(w121), .c(w76), .d(w77), .x(w73) );
	ula_nor g128 (.a(w31), .b(w75), .x(w78) );
	ula_nor g129 (.a(w76), .b(w78), .x(w31) );

	ula_nor g104 (.b(w78), .a(w79), .x(w81) );

endmodule // hcounter

module vcounter ();
	wire w138;
	wire w142;
	wire w158;
	wire w159;
	wire w194;
	wire w262;
	wire w301;
	wire w306;

	// 0
	ula_not g9 (.a(w81), .x(w23) );
	ula_nor g140 (.a(w25), .b(w37), .x(w24) );
	ula_nor g141 (.a(w38), .b(w24), .x(w25) );
	ula_nor g142 (.a(w24), .b(w23), .x(w40) );
	ula_nor g143 (.a(w81), .b(w25), .x(w39) );
	ula_nor g144 (.a(w34), .b(w35), .x(w37) );
	ula_nor g145 (.a(w37), .b(w34), .x(w38) );
	ula_nor3 g146 (.a(w39), .b(w40), .c(w38), .x(w36) );
	ula_nor g147 (.a(w23), .b(w24), .x(w88) );
	ula_nor g148 (.a(w37), .b(w36), .x(w35) );
	// 1
	ula_not g11 (.a(w88), .x(w141) );
	ula_nor g139 (.a(w141), .b(w140), .x(w160) );
	ula_nor g149 (.a(w89), .b(w138), .x(w90) );
	ula_nor g157 (.a(w90), .b(w34), .x(w89) );
	ula_nor g158 (.a(w89), .b(w34), .x(w142) );
	ula_nor3 g159 (.a(w142), .b(w139), .c(w87), .x(w138) );
	ula_nor g160 (.a(w86), .b(w88), .x(w87) );
	ula_nor g161 (.a(w140), .b(w142), .x(w86) );
	ula_nor g162 (.a(w140), .b(w141), .x(w139) );
	ula_nor g163 (.a(w86), .b(w89), .x(w140) );	
	// 2
	ula_not g13 (.a(w160), .x(w93) );
	ula_nor g132 (.a(w92), .b(w95), .x(w91) );
	ula_nor3 g134 (.a(w95), .b(w159), .c(w94), .x(w158) );
	ula_nor g135 (.a(w91), .b(w160), .x(w159) );
	ula_nor g136 (.a(w158), .b(w97), .x(w96) );
	ula_nor g137 (.a(w96), .b(w34), .x(w97) );
	ula_nor g138 (.a(w34), .b(w97), .x(w95) );
	ula_nor g164 (.a(w92), .b(w93), .x(w94) );
	ula_nor g165 (.a(w91), .b(w97), .x(w92) );
	ula_nor g166 (.a(w92), .b(w93), .x(w98) );
	// 3 - not sure 
	ula_nor g537 (.a(w297), .b(w293), .x(w279) );
	ula_nor g538 (.a(w293), .b(w278), .x(w296) );
	ula_nor4 g539 (.a(w295), .b(w296), .c(w277), .d(w297), .x(w312) );
	ula_nor g550 (.a(w193), .b(w280), .x(w297) );
	ula_nor g551 (.a(w193), .b(w281), .x(w280) );
	ula_nor g552 (.a(w280), .b(w312), .x(w281) );	
	ula_nor g553 (.a(w279), .b(w280), .x(w293) );
	ula_nor g540 (.a(w293), .b(w278), .x(w292) );
	// 4
	ula_not g88 (.a(w292), .x(w288) );
	ula_nor g541 (.a(w292), .b(w187), .x(w289) );
	ula_nor g542 (.a(w291), .b(w288), .x(w290) );
	ula_nor g543 (.a(w193), .b(w185), .x(w308) );
	ula_nor g544 (.a(w193), .b(w308), .x(w186) );
	ula_nor g545 (.a(w184), .b(w308), .x(w185) );	
	ula_nor4 g547 (.a(w295), .b(w289), .c(w186), .d(w290), .x(w184) );
	ula_nor g548 (.a(w187), .b(w308), .x(w291) );
	ula_nor g549 (.a(w186), .b(w291), .x(w187) );
	ula_nor g568 (.a(w291), .b(w288), .x(w287) );	

	// not sure
	ula_not g93 (.a(w287), .x(w294) );
	ula_nor g572 (.a(w294), .b(w286), .x(w174) );
	ula_nor g574 (.a(w287), .b(w179), .x(w306) );	
	ula_nor g523 (.a(w228), .b(w221), .x(w193) );
	ula_not g89 (.a(w98), .x(w278) );
	ula_nor4 g567 (.a(w286), .b(w291), .c(w311), .d(w278), .x(w295) );
	ula_nor g536 (.a(w279), .b(w98), .x(w277) );

	// 5 - not sure
	ula_nor4 g569 (.a(w180), .b(w181), .c(w295), .d(w306), .x(w307) );
	ula_nor g570 (.a(w193), .b(w183), .x(w182) );
	ula_nor g571 (.a(w193), .b(w182), .x(w181) );
	ula_nor g573 (.a(w294), .b(w286), .x(w180) );
	ula_nor g575 (.a(w181), .b(w286), .x(w179) );
	ula_nor g576 (.a(w179), .b(w182), .x(w286) );
	ula_nor g546 (.a(w307), .b(w182), .x(w183) );	

	// 6
	ula_not g94 (.a(w174), .x(w175) );
	ula_nor g598 (.a(w282), .b(w178), .x(w270) );
	ula_nor g599 (.a(w283), .b(w270), .x(w178) );
	ula_nor g600 (.a(w174), .b(w178), .x(w177) );
	ula_nor g601 (.a(w270), .b(w175), .x(w176) );
	ula_nor g602 (.a(w193), .b(w282), .x(w283) );
	ula_nor g603 (.a(w193), .b(w192), .x(w282) );
	ula_nor g604 (.a(w305), .b(w282), .x(w192) );
	ula_nor3 g605 (.a(w177), .b(w176), .c(w283), .x(w305) );
	ula_nor g606 (.a(w175), .b(w270), .x(w285) );

	// 7
	ula_not g97 (.a(w285), .x(w268) );
	ula_nor g595 (.a(w304), .b(w269), .x(w272) );
	ula_nor g596 (.a(w272), .b(w285), .x(w284) );
	ula_nor3 g597 (.a(w304), .b(w284), .c(w300), .x(w301) );
	ula_nor g607 (.a(w193), .b(w303), .x(w304) );
	ula_nor g608 (.a(w302), .b(w193), .x(w303) );
	ula_nor g609 (.a(w301), .b(w303), .x(w302) );
	ula_nor g610 (.a(w268), .b(w269), .x(w300) );
	ula_nor g611 (.a(w303), .b(w272), .x(w269) );
	ula_nor g612 (.a(w268), .b(w269), .x(w267) );

	// 8
	ula_not g95 (.a(w267), .x(w265) );
	ula_nor g577 (.a(w193), .b(w262), .x(w194) );
	ula_nor g578 (.a(w326), .b(w193), .x(w262) );
	ula_nor g579 (.a(w263), .b(w262), .x(w326) );
	ula_nor g580 (.a(w261), .b(w267), .x(w266) );
	ula_nor g581 (.a(w265), .b(w311), .x(w264) );
	ula_nor g564 (.a(w261), .b(w262), .x(w311) );
	ula_nor g565 (.a(w194), .b(w311), .x(w261) );
	ula_nor4 g566 (.a(w264), .b(w266), .c(w194), .d(w295), .x(w263) );

endmodule // vcounter

module tclk (input wire nMREQ, input wire nIOREQ, input wire nRD, input wire nWR, output wire WR, output wire nTCLKA, output wire nTCLKB, output wire K0);
	wire w313;

	ula_not g81 (.a(w244), .x(w318) );
	ula_nor4 g527 (.a(nMREQ), .b(nIOREQ), .c(w318), .d(w309), .x(w228) );
	ula_not g82 (.a(w309), .x(w238) );
	ula_nor4 g525 (.a(w238), .b(w244), .c(nMREQ), .d(nIOREQ), .x(w235) );
	ula_not g83 (.a(w235), .x(w313) );	
	ula_nor g528 (.a(w311), .b(w313), .x(w276) );
endmodule // tclk

module latch_control (input wire nCLK7, inout wire Border);
	wire w387;
	wire w390;
	wire w392;
	wire w397;

	ula_not g49 (.a(w260), .x(Border) );
	ula_nor g422 (.a(w203), .b(Border), .x(w349) );
	ula_not g50 (.a(w349), .x(w330) );

	ula_not g55 (.a(nCLK7), .x(w389) );
	ula_not g56 (.a(w389), .x(w390) );
	ula_nor g429 (.a(w390), .b(w390), .x(w391) );
	ula_nor g428 (.a(w391), .b(w391), .x(w392) );	
	ula_not g58 (.a(w392), .x(w393) );
	ula_not g59 (.a(w393), .x(w394) );
	ula_nor g449 (.a(w394), .b(w336), .x(w366) );

	ula_nor4 g427 (.a(w72), .b(w336), .c(w366), .d(w330), .x(w396) );	
	ula_nor g408 (.a(w396), .b(w396), .x(w397) );
	ula_nor g409 (.a(w397), .b(w397), .x(w398) );
	ula_not g51 (.a(w398), .x(w447) );

	// GD
	ula_nor g480 (.a(w388), .b(w203), .x(w387) );
	ula_nor g481 (.a(w203), .b(w260), .x(w388) );
	ula_nor g466 (.a(w350), .b(w388), .x(w351) );
	ula_nor g467 (.a(w387), .b(w351), .x(w350) );

	ula_not g57 (.a(w336), .x(w367) );
	ula_nor4 g443 (.a(w72), .b(w234), .c(w350), .d(w367), .x(w357) );	
	ula_not g339 (.a(w357), .x(w549) );

	ula_nor4 g407 (.a(w336), .b(w330), .c(w331), .d(w366), .x(w419) );
	ula_not g47 (.a(w419), .x(w418) );

	ula_nor3 g406 (.a(w72), .b(w336), .c(w234), .x(w339) );
	ula_not g46 (.a(w339), .x(w340) );
endmodule // latch_control

module data_latch ();
	wire w518;
	wire w523;
	wire w533;
	wire w548;
	wire w598;
	wire w605;
	wire w621;
	wire w633;

	// 0
	ula_nor g219 (.a(w7), .b(w447), .x(w620) );
	ula_nor g220 (.a(w620), .b(w479), .x(w621) );
	ula_nor g247 (.a(w621), .b(w619), .x(w479) );
	ula_nor g248 (.a(w620), .b(w447), .x(w619) );
	// 1
	ula_nor g251 (.a(w478), .b(w447), .x(w533) );
	ula_nor g252 (.a(w533), .b(w532), .x(w583) );
	ula_nor g282 (.a(w583), .b(w534), .x(w532) );
	ula_nor g283 (.a(w447), .b(w533), .x(w534) );
	// 2 
	ula_nor g285 (.a(w512), .b(w447), .x(w599) );
	ula_nor g286 (.a(w599), .b(w596), .x(w597) );
	ula_nor g315 (.a(w597), .b(w598), .x(w596) );
	ula_nor g316 (.a(w447), .b(w599), .x(w598) );
	// 3 
	ula_nor g318 (.a(w447), .b(w608), .x(w607) );
	ula_nor g319 (.a(w607), .b(w593), .x(w605) );
	ula_nor g345 (.a(w606), .b(w605), .x(w593) );
	ula_nor g346 (.a(w447), .b(w607), .x(w606) );
	// 4
	ula_nor g375 (.a(w524), .b(w521), .x(w523) );
	ula_nor g376 (.a(w522), .b(w447), .x(w521) );
	ula_nor g377 (.a(w521), .b(w447), .x(w481) );
	ula_nor g378 (.a(w481), .b(w523), .x(w524) );
	// 5
	ula_nor g369 (.a(w498), .b(w447), .x(w499) );
	ula_nor g370 (.a(w447), .b(w416), .x(w498) );
	ula_nor g347 (.a(w498), .b(w632), .x(w633) );
	ula_nor g348 (.a(w499), .b(w633), .x(w632) );
	// 6
	ula_nor g365 (.a(w500), .b(w447), .x(w547) );
	ula_nor g366 (.a(w447), .b(w516), .x(w500) );
	ula_nor g351 (.a(w500), .b(w501), .x(w548) );
	ula_nor g352 (.a(w547), .b(w548), .x(w501) );
	// 7
	ula_nor g361 (.a(w447), .b(w520), .x(w519) );
	ula_nor g362 (.a(w447), .b(w417), .x(w520) );
	ula_nor g355 (.a(w517), .b(w520), .x(w518) );
	ula_nor g356 (.a(w519), .b(w518), .x(w517) );
endmodule // data_latch

module attr_latch ();
	wire w482;
	wire w497;
	wire w525;
	wire w526;
	wire w543;
	wire w544;
	wire w545;
	wire w552;
	wire w553;
	wire w600;
	wire w601;
	wire w602;
	wire w603;
	wire w604;
	wire w609;
	wire w616;
	wire w618;

	// +paper/border mux

	// 0
	ula_nor g221 (.a(w7), .b(w418), .x(w617) );
	ula_nor g222 (.a(w617), .b(w616), .x(w506) );
	ula_nor g245 (.a(w618), .b(w506), .x(w616) );
	ula_nor g246 (.a(w617), .b(w418), .x(w618) );
	// 1
	ula_nor g253 (.a(w478), .b(w418), .x(w615) );
	ula_nor g254 (.a(w615), .b(w613), .x(w585) );
	ula_nor g280 (.a(w584), .b(w585), .x(w613) );
	ula_nor g281 (.a(w615), .b(w418), .x(w584) );
	// 2
	ula_nor g313 (.a(w575), .b(w601), .x(w574) );
	ula_nor g314 (.a(w418), .b(w600), .x(w601) );
	ula_nor g287 (.a(w418), .b(w512), .x(w600) );
	ula_nor g288 (.a(w600), .b(w574), .x(w575) );
	// 3
	ula_nor g343 (.a(w491), .b(w604), .x(w603) );
	ula_nor g344 (.a(w418), .b(w602), .x(w604) );
	ula_nor g320 (.a(w608), .b(w418), .x(w602) );
	ula_nor g321 (.a(w602), .b(w603), .x(w491) );
	// 4
	ula_nor g379 (.a(w525), .b(w418), .x(w482) );
	ula_nor g380 (.a(w482), .b(w527), .x(w526) );	
	ula_nor g373 (.a(w526), .b(w525), .x(w527) );
	ula_nor g374 (.a(w418), .b(w522), .x(w525) );
	// 5
	ula_nor g349 (.a(w495), .b(w496), .x(w494) );
	ula_nor g350 (.a(w497), .b(w494), .x(w495) );
	ula_nor g367 (.a(w496), .b(w418), .x(w497) );
	ula_nor g368 (.a(w418), .b(w416), .x(w496) );
	// 6
	ula_nor g353 (.a(w544), .b(w546), .x(w543) );
	ula_nor g354 (.a(w545), .b(w543), .x(w544) );
	ula_nor g363 (.a(w546), .b(w418), .x(w545) );
	ula_nor g364 (.a(w418), .b(w516), .x(w546) );
	// 7
	ula_nor g357 (.a(w539), .b(w540), .x(w542) );
	ula_nor g358 (.a(w541), .b(w542), .x(w540) );
	ula_nor g359 (.a(w418), .b(w539), .x(w541) );
	ula_nor g360 (.a(w417), .b(w418), .x(w539) );


	// R
	ula_nor g258 (.a(w351), .b(w610), .x(w609) );
	ula_nor g324 (.a(w527), .b(w528), .x(w553) );
	ula_nor g325 (.a(w553), .b(w609), .x(w554) );
	// G
	ula_nor g277 (.a(w570), .b(w351), .x(w569) );
	ula_nor g292 (.a(w493), .b(w569), .x(w568) );
	ula_nor g340 (.a(w528), .b(w494), .x(w493) );
	// B
	ula_nor g310 (.a(w491), .b(w528), .x(w492) );
	ula_nor g291 (.a(w492), .b(w511), .x(w622) );
	ula_nor g257 (.a(w510), .b(w351), .x(w511) );

	// FL
	ula_not g32 (.a(w351), .x(w528) );
	ula_not g35 (.a(w542), .x(w552) );
	ula_nor g326 (.a(w528), .b(w552), .x(w631) );	

	// HL
	ula_not g34 (.a(w543), .x(w551) );
	ula_nor g309 (.a(w551), .b(w528), .x(w550) );

endmodule // data_latch

module ao_latch (inout wire FL);
	wire w502;
	wire w505;
	wire w555;
	wire w557;
	wire w586;
	wire w591;
	wire w626;
	wire w628;
	wire w648;

	// 0
	ula_nor g225 (.a(w506), .b(w340), .x(w505) );
	ula_nor g226 (.a(w340), .b(w505), .x(w504) );
	ula_nor g227 (.a(w590), .b(w504), .x(w591) );
	ula_nor g228 (.a(w505), .b(w591), .x(w590) );
	// 1
	ula_nor g273 (.a(w623), .b(w626), .x(w624) );
	ula_nor g274 (.a(w627), .b(w624), .x(w626) );
	ula_nor g275 (.a(w340), .b(w623), .x(w627) );
	ula_nor g276 (.a(w340), .b(w622), .x(w623) );
	// 2
	ula_nor g239 (.a(w586), .b(w589), .x(w588) );
	ula_nor g240 (.a(w588), .b(w587), .x(w589) );
	ula_nor g241 (.a(w587), .b(w340), .x(w586) );
	ula_nor g242 (.a(w340), .b(w585), .x(w587) );
	// 3
	ula_nor g293 (.a(w554), .b(w340), .x(w555) );
	ula_nor g294 (.a(w340), .b(w555), .x(w556) );
	ula_nor g295 (.a(w556), .b(w558), .x(w557) );
	ula_nor g296 (.a(w555), .b(w557), .x(w558) );
	// 4
	ula_nor g259 (.a(w575), .b(w340), .x(w576) );
	ula_nor g260 (.a(w340), .b(w576), .x(w577) );
	ula_nor g261 (.a(w577), .b(w579), .x(w578) );
	ula_nor g262 (.a(w576), .b(w578), .x(w579) );
	// 5
	ula_nor g305 (.a(w565), .b(w566), .x(w564) );
	ula_nor g306 (.a(w567), .b(w564), .x(w565) );
	ula_nor g307 (.a(w340), .b(w566), .x(w567) );
	ula_nor g308 (.a(w340), .b(w568), .x(w566) );
	// 6
	ula_nor g327 (.a(w340), .b(w550), .x(w629) );
	ula_nor g328 (.a(w629), .b(w340), .x(w630) );
	ula_nor g329 (.a(w630), .b(w14), .x(w628) );
	ula_nor g330 (.a(w629), .b(w628), .x(w14) );
	// 7
	ula_nor g303 (.a(FL), .b(w503), .x(w648) );
	ula_nor g304 (.a(w502), .b(w648), .x(FL) );
	ula_nor g331 (.a(w631), .b(w340), .x(w502) );
	ula_nor g332 (.a(w340), .b(w502), .x(w503) );
endmodule // ao_latch

module pixel_shift_reg (input wire nCLK7);
	wire w341;
	wire w356;
	wire w370;
	wire w454;
	wire w456;
	wire w463;
	wire w464;
	wire w466;
	wire w467;
	wire w470;
	wire w473;
	wire w475;
	wire w530;
	wire w531;
	wire w595;
	wire w634;
	wire w635;
	wire w636;
	wire w637;
	wire w641;
	wire w649;

	ula_not g62 (.a(nCLK7), .x(w379) );
	// 0
	ula_nor3 g232 (.a(w479), .b(w549), .c(w355), .x(w529) );
	ula_nor g233 (.a(w353), .b(w529), .x(w352) );
	ula_nor g482 (.a(w357), .b(w356), .x(w450) );
	ula_nor g483 (.a(w355), .b(w356), .x(w354) );
	ula_nor g484 (.a(w354), .b(w353), .x(w356) );
	ula_nor g485 (.a(w379), .b(w353), .x(w355) );
	ula_nor g486 (.a(w352), .b(w379), .x(w353) );
	// 1
	ula_nor g234 (.a(w451), .b(w530), .x(w455) );
	ula_nor3 g235 (.a(w531), .b(w450), .c(w452), .x(w530) );
	ula_nor g236 (.a(w532), .b(w549), .x(w531) );
	ula_nor g461 (.a(w379), .b(w455), .x(w451) );
	ula_nor g462 (.a(w451), .b(w379), .x(w452) );
	ula_nor g463 (.a(w451), .b(w454), .x(w456) );
	ula_nor g464 (.a(w456), .b(w452), .x(w454) );
	ula_nor g465 (.a(w454), .b(w357), .x(w453) );
	// 2
	ula_nor g267 (.a(w549), .b(w596), .x(w641) );
	ula_nor3 g268 (.a(w641), .b(w453), .c(w377), .x(w642) );
	ula_nor g269 (.a(w375), .b(w642), .x(w376) );
	ula_nor g456 (.a(w374), .b(w357), .x(w373) );
	ula_nor g457 (.a(w377), .b(w378), .x(w374) );
	ula_nor g458 (.a(w375), .b(w374), .x(w378) );
	ula_nor g459 (.a(w379), .b(w375), .x(w377) );
	ula_nor g460 (.a(w376), .b(w379), .x(w375) );
	// 3
	ula_nor g270 (.a(w369), .b(w595), .x(w372) );
	ula_nor3 g271 (.a(w370), .b(w373), .c(w594), .x(w595) );
	ula_nor g272 (.a(w593), .b(w549), .x(w594) );
	ula_nor g438 (.a(w379), .b(w372), .x(w369) );
	ula_nor g439 (.a(w379), .b(w369), .x(w370) );
	ula_nor g440 (.a(w369), .b(w368), .x(w371) );
	ula_nor g441 (.a(w371), .b(w370), .x(w368) );
	ula_nor g442 (.a(w368), .b(w357), .x(w475) );

	ula_not g53 (.a(nCLK7), .x(w381) );
	// 4
	ula_nor g297 (.a(w549), .b(w524), .x(w649) );
	ula_nor3 g298 (.a(w649), .b(w475), .c(w470), .x(w650) );
	ula_nor g299 (.a(w469), .b(w650), .x(w474) );
	ula_nor g433 (.a(w472), .b(w357), .x(w473) );
	ula_nor g434 (.a(w470), .b(w471), .x(w472) );
	ula_nor g435 (.a(w472), .b(w469), .x(w471) );
	ula_nor g436 (.a(w381), .b(w469), .x(w470) );
	ula_nor g437 (.a(w474), .b(w381), .x(w469) );
	// 5
	ula_nor g300 (.a(w639), .b(w464), .x(w468) );
	ula_nor3 g301 (.a(w463), .b(w473), .c(w638), .x(w639) );
	ula_nor g302 (.a(w632), .b(w549), .x(w638) );
	ula_nor g417 (.a(w381), .b(w468), .x(w464) );
	ula_nor g418 (.a(w464), .b(w381), .x(w463) );
	ula_nor g419 (.a(w464), .b(w466), .x(w465) );
	ula_nor g420 (.a(w465), .b(w463), .x(w466) );
	ula_nor g421 (.a(w466), .b(w357), .x(w467) );
	// 6
	ula_nor g333 (.a(w549), .b(w501), .x(w636) );
	ula_nor3 g334 (.a(w636), .b(w467), .c(w460), .x(w637) );
	ula_nor g335 (.a(w459), .b(w637), .x(w461) );
	ula_nor g412 (.a(w458), .b(w357), .x(w457) );
	ula_nor g413 (.a(w460), .b(w462), .x(w458) );
	ula_nor g414 (.a(w459), .b(w458), .x(w462) );
	ula_nor g415 (.a(w381), .b(w459), .x(w460) );
	ula_nor g416 (.a(w461), .b(w381), .x(w459) );
	// 7
	ula_nor g336 (.a(w635), .b(w341), .x(w382) );
	ula_nor3 g337 (.a(w343), .b(w457), .c(w634), .x(w635) );
	ula_nor g338 (.a(w517), .b(w549), .x(w634) );
	ula_nor g398 (.a(w381), .b(w382), .x(w341) );
	ula_nor g399 (.a(w341), .b(w381), .x(w343) );
	ula_nor g400 (.a(w341), .b(w342), .x(w197) );
	ula_nor g401 (.a(w343), .b(w197), .x(w342) );
endmodule // pixel_shift_reg

module flash_clock (input wire nTCLKB, output wire FlashClock);
	wire w44;
	wire w155;
	wire w170;

	ula_nor g529 (.a(w235), .b(w311), .x(w33) );	
	// 0
	ula_nor g180 (.a(w33), .b(w43), .x(w32) );
	ula_nor g181 (.a(w50), .b(w33), .x(w43) );
	ula_nor g207 (.a(w49), .b(w43), .x(w50) );
	ula_nor g208 (.a(w32), .b(w46), .x(w49) );	
	ula_nor g209 (.a(w43), .b(w46), .x(w47) );
	ula_nor g210 (.a(w32), .b(w47), .x(w46) );
	// 1
	ula_nor g182 (.a(w47), .b(w42), .x(w41) );
	ula_nor g183 (.a(w48), .b(w47), .x(w42) );
	ula_nor g203 (.a(w155), .b(w42), .x(w48) );
	ula_nor g204 (.a(w42), .b(w44), .x(w45) );
	ula_nor g205 (.a(w41), .b(w44), .x(w155) );
	ula_nor g206 (.a(w41), .b(w45), .x(w44) );
	// 2
	ula_nor g184 (.a(w45), .b(w60), .x(w63) );
	ula_nor g185 (.a(w61), .b(w45), .x(w60) );
	ula_nor g199 (.a(w156), .b(w60), .x(w61) );
	ula_nor g200 (.a(w60), .b(w62), .x(w59) );
	ula_nor g201 (.a(w63), .b(w62), .x(w156) );
	ula_nor g202 (.a(w63), .b(w59), .x(w62) );
	// 3
	ula_nor g186 (.a(w59), .b(w162), .x(w161) );
	ula_nor g187 (.a(w166), .b(w59), .x(w162) );	
	ula_nor g195 (.a(w162), .b(w169), .x(w167) );
	ula_nor g196 (.a(w171), .b(w162), .x(w166) );
	ula_nor g197 (.a(w161), .b(w169), .x(w171) );
	ula_nor g198 (.a(w161), .b(w167), .x(w169) );
	// 4
	ula_nor g188 (.a(w167), .b(w163), .x(w164) );
	ula_nor g189 (.a(w167), .b(w165), .x(w163) );
	ula_nor g191 (.a(w172), .b(w163), .x(w165) );
	ula_nor g192 (.a(w163), .b(w170), .x(w168) );
	ula_nor g193 (.a(w164), .b(w170), .x(w172) );
	ula_nor g194 (.a(w164), .b(w168), .x(w170) );
endmodule // flash_clock

module flash_xnor (input wire FL, input wire FlashClock, output wire nDataSelect);
	wire w195;

	ula_not g79 (.a(FL), .x(w195) );	
	ula_nor g516 (.a(w199), .b(w196), .x(w64) );
	ula_nor g517 (.a(w195), .b(w168), .x(w196) );	
	ula_nor g487 (.a(w197), .b(w199), .x(w65) );
	ula_nor g488 (.a(w196), .b(w197), .x(w199) );
	ula_nor g190 (.a(w64), .b(w65), .x(w66) );
endmodule // flash_xnor

module color_mux (input wire nHBlank, output wire Red, output wire Green, output wire Blue);
	wire w559;
	wire w560;
	wire w561;
	wire w562;
	wire w563;
	wire w625;

	ula_not g27 (.a(w67), .x(w480) );

	ula_not g31 (.a(w66), .x(w559) );
	ula_nor g265 (.a(w558), .b(w559), .x(w563) );
	ula_nor g230 (.a(w589), .b(w66), .x(w592) );
	ula_nor4 g231 (.a(w30), .b(w592), .c(w480), .d(w563), .x(w51) );

	ula_not g28 (.a(w66), .x(w625) );
	ula_not g30 (.a(w66), .x(w640) );
	ula_nor g264 (.a(w625), .b(w624), .x(w562) );
	ula_nor g266 (.a(w564), .b(w640), .x(w560) );
	ula_nor4 g237 (.a(w480), .b(w560), .c(w561), .d(w30), .x(w56) );
	
	ula_nor g263 (.a(w579), .b(w66), .x(w561) );
	ula_nor g229 (.a(w66), .b(w590), .x(w643) );
	ula_nor4 g238 (.a(w480), .b(w643), .c(w562), .d(w30), .x(w18) );
endmodule // color_mux

module video_addr_gen ();
	wire w100;
	wire w114;
	wire w213;
	wire w214;
	wire w215;
	wire w218;
	wire w254;
	wire w255;
	wire w256;
	wire w257;
	wire w299;
	wire w319;
	wire w321;
	wire w324;
	wire w325;

	ula_not g69 (.a(w427), .x(w423) );

	ula_not g73 (.a(w423), .x(w424) );
	ula_not g72 (.a(w424), .x(w102) );
	ula_not g12 (.a(w72), .x(w101) );
	ula_nor g556 (.a(w102), .b(w72), .x(w114) );
	ula_nor g130 (.a(w101), .b(w102), .x(w100) );
	ula_not g90 (.a(w102), .x(w217) );
	ula_not g7 (.a(w114), .x(w115) );
	ula_not g8 (.a(w100), .x(w99) );

	ula_nor g530 (.a(w208), .b(w208), .x(w210) );
	ula_not g86 (.a(w210), .x(w211) );
	ula_not g85 (.a(w211), .x(w212) );
	ula_nor g535 (.a(w212), .b(w212), .x(w213) );
	ula_nor g554 (.a(w213), .b(w213), .x(w214) );
	ula_nor g563 (.a(w214), .b(w214), .x(w215) );
	ula_nor g582 (.a(w215), .b(w215), .x(w216) );

	ula_nor g593 (.a(w217), .b(w216), .x(w299) );
	ula_nor g616 (.a(w179), .b(w115), .x(w256) );
	ula_nor g617 (.a(w99), .b(w179), .x(w257) );
	ula_nor3 g615 (.a(w256), .b(w257), .c(w299), .x(w173) );	

	// 2
	ula_nor g583 (.a(w112), .b(w217), .x(w319) );
	ula_nor g585 (.a(w115), .b(w86), .x(w320) );
	ula_nor g586 (.a(w272), .b(w99), .x(w321) );	
	ula_nor3 g584 (.a(w320), .b(w321), .c(w319), .x(w327) );

	// 5
	ula_nor g560 (.a(w272), .b(w115), .x(w324) );
	ula_nor g561 (.a(w217), .b(w279), .x(w325) );
	ula_nor g558 (.a(w325), .b(w324), .x(w274) );

	// 1
	ula_nor g590 (.a(w178), .b(w99), .x(w254) );
	ula_nor g591 (.a(w115), .b(w25), .x(w255) );
	ula_nor g594 (.a(w217), .b(w113), .x(w298) );	
	ula_nor3 g592 (.a(w298), .b(w254), .c(w255), .x(w191) );

	// 3
	ula_nor g588 (.a(w17), .b(w217), .x(w218) );
	ula_nor g589 (.a(w91), .b(w115), .x(w219) );
	ula_not g96 (.a(w99), .x(w258) );
	ula_nor3 g618 (.a(w218), .b(w219), .c(w258), .x(w323) );	

	// 4
	ula_nor g557 (.a(w16), .b(w217), .x(w273) );
	ula_nor g559 (.a(w115), .b(w178), .x(w328) );
	ula_nor g587 (.a(w273), .b(w328), .x(w322) );
	
	// 6
	ula_not g91 (.a(w115), .x(w189) );
	ula_not g92 (.a(w99), .x(w190) );
	ula_nor g562 (.a(w187), .b(w217), .x(w188) );
	ula_nor3 g555 (.a(w189), .b(w190), .c(w188), .x(w275) );	
endmodule // video_addr_gen

module address_enable (input wire [8:0] nC, input wire Border, output wire nAE);
	ula_nor3 g426 (.a(w336), .b(w234), .c(w331), .x(w399) );
	ula_nor g410 (.a(w253), .b(w399), .x(w363) );	
	ula_nor g391 (.a(Border), .b(w363), .x(w420) );
	ula_not g661 (.a(w420), .x(nAE) );	
endmodule // address_enable

module ras_cas_romcs (input wire A14, input wire A15, input wire nMREQ);
	ula_not g40 (.a(A14), .x(w406) );
	ula_nor3 g389 (.a(w406), .b(A15), .c(nMREQ), .x(w242) );

	ula_not g71 (.a(w336), .x(w403) );
	ula_not g63 (.a(w403), .x(w402) );
	ula_not g60 (.a(w402), .x(w401) );
	ula_not g64 (.a(w401), .x(w400) );
	ula_nor3 g448 (.a(w336), .b(w331), .c(w400), .x(w395) );
	ula_nor g451 (.a(w395), .b(w330), .x(w427) );

	ula_nor g500 (.a(w242), .b(w242), .x(w241) );
	ula_nor g502 (.a(w241), .b(w241), .x(w240) );
	ula_nor g504 (.a(w240), .b(w240), .x(w245) );
	ula_nor g501 (.a(w318), .b(w238), .x(w239) );
	ula_nor g503 (.a(w239), .b(w245), .x(w246) );

	ula_nor g526 (.a(w245), .b(w244), .x(w315) );
	ula_not g87 (.a(w315), .x(w316) );
	ula_nor g390 (.a(w427), .b(w242), .x(w439) );
	ula_nor g387 (.a(A15), .b(A14), .x(w408) );
	ula_nor4 g388 (.a(A15), .b(A14), .c(w260), .d(nMREQ), .x(w438) );
	ula_not g39 (.a(w408), .x(w409) );

	ula_nor g450 (.a(w72), .b(w72), .x(w428) );
	ula_not g65 (.a(w428), .x(w429) );
	ula_not g66 (.a(w429), .x(w432) );
	ula_nor g473 (.a(w423), .b(w423), .x(w431) );
	ula_nor g474 (.a(w431), .b(w431), .x(w430) );
	ula_nor3 g475 (.a(w366), .b(w330), .c(w432), .x(w433) );
	ula_nor4 g477 (.a(w72), .b(w330), .c(w430), .d(w366), .x(w434) );

	// CAS
	ula_nor g506 (.a(w246), .b(w246), .x(w247) );
	ula_nor g505 (.a(w247), .b(w247), .x(w248) );	
	ula_nor3 g476 (.a(w248), .b(w434), .c(w433), .x(w435) );
	ula_not g75 (.a(w435), .x(w436) );
	ula_not g76 (.a(w436), .x(w437) );
	ula_not g67 (.a(w437), .x(w364) );
	ula_not g68 (.a(w364), .x(w365) );
	ula_not g70 (.a(w365), .x(w422) );
	ula_not g74 (.a(w422), .x(w421) );
endmodule // ras_cas_romcs

module video_signal_features ();
	wire w252;
	wire w271;	

	ula_nor g613 (.a(w269), .b(w270), .x(w271) );
	ula_nor3 g614 (.a(w31), .b(w261), .c(w271), .x(w260) );

	ula_nor g167 (.a(1'b0), .b(w112), .x(w110) );
	ula_nor g168 (.a(w110), .b(w110), .x(w109) );
	ula_nor g169 (.a(1'b0), .b(w109), .x(w107) );
	ula_nor g170 (.a(w107), .b(w107), .x(w106) );
	ula_nor g171 (.a(1'b0), .b(w106), .x(w104) );
	ula_nor g172 (.a(w104), .b(w104), .x(w103) );

	ula_nor3 g531 (.a(w221), .b(w203), .c(w227), .x(w250) );
	ula_nor g532 (.a(w203), .b(w227), .x(w249) );
	ula_nor g533 (.a(w112), .b(w249), .x(w251) );
	ula_nor g534 (.a(w251), .b(w250), .x(w252) );
	ula_not g84 (.a(w252), .x(w71) );

	ula_nor4 g105 (.a(w70), .b(w16), .c(w78), .d(w71), .x(w118) );
	ula_nor g106 (.a(w30), .b(w118), .x(w29) );

	ula_nor3 g107 (.a(w16), .b(w78), .c(w70), .x(w69) );
	ula_nor g131 (.a(w69), .b(w68), .x(w67) );
	ula_nor3 g133 (.a(w78), .b(w79), .c(w103), .x(w68) );

	ula_nor g119 (.a(w29), .b(w21), .x(w20) );
	ula_nor g120 (.a(w29), .b(w25), .x(w21) );
	ula_nor g150 (.a(w21), .b(w19), .x(w22) );
	ula_nor g151 (.a(w22), .b(w20), .x(w19) );

	ula_nor6 g621 (.a(w270), .b(w269), .c(w91), .d(w293), .e(w291), .f(w286), .x(w30) );

	ula_nor5 g620 (.a(w78), .b(w79), .c(w113), .d(w17), .e(w103), .x(w143) );
	ula_not g3 (.a(w30), .x(w119) );
	ula_nor7 g619 (.a(w17), .b(w16), .c(w119), .d(w86), .e(w91), .f(w25), .g(w31), .x(w116) );
	ula_not g4 (.a(w116), .x(w117) );
	ula_not g14 (.a(w143), .x(w134) );
	ula_nor g118 (.a(w134), .b(w19), .x(w135) );
	ula_not g6 (.a(w135), .x(w136) );
	ula_not g10 (.a(w143), .x(w146) );
	ula_nor g117 (.b(w22), .a(w134), .x(w137) );
endmodule // video_signal_features

module dac_setup (output wire BlueD, output wire RedD, output wire nRedDD);
	wire w125;
	wire w128;
	wire w152;

	ula_not g2 (.a(w29), .x(w123) );
	ula_not g5 (.a(w123), .x(w124) );
	ula_not g23 (.a(w14), .x(w5) );
	ula_nor3 g174 (.a(w130), .b(w3), .c(w128), .x(w129) );
	ula_nor3 g211 (.a(w56), .b(w51), .c(w18), .x(w152) );
	ula_not g19 (.a(w129), .x(w4) );

	// R
	ula_nor g212 (.a(w51), .b(w19), .x(w53) );
	ula_nor g176 (.a(w127), .b(w126), .x(w128) );
	ula_nor g177 (.a(w53), .b(w19), .x(w127) );
	ula_nor g178 (.a(w53), .b(w51), .x(w126) );	
	ula_nor g624 (.a(w129), .b(w128), .x(w133) );
	ula_not g1 (.a(w133), .x(w132) );	
	ula_nor g173 (.a(w152), .b(w51), .x(nRedDD) );
	ula_not g18 (.a(w51), .x(w125) );
	ula_not g15 (.a(w125), .x(RedD) );

	// G
	ula_nor g213 (.a(w19), .b(w56), .x(w52) );
	ula_nor g215 (.a(w56), .b(w52), .x(w55) );
	ula_nor g216 (.a(w52), .b(w19), .x(w54) );
	ula_nor g175 (.a(w55), .b(w54), .x(w3) );
	ula_nor g153 (.a(w3), .b(w129), .x(w144) );
	ula_nor g179 (.a(w56), .b(w152), .x(w147) );
	ula_not g17 (.a(w56), .x(w153) );
	ula_not g16 (.a(w153), .x(w154) );

	// B
	ula_nor g154 (.a(w149), .b(w18), .x(w151) );
	ula_nor g155 (.a(w18), .b(w19), .x(w149) );
	ula_nor g156 (.a(w149), .b(w19), .x(w150) );
	ula_nor g152 (.a(w151), .b(w150), .x(w130) );
	ula_nor g625 (.a(w129), .b(w130), .x(w145) );	
	ula_not g22 (.a(w18), .x(w15) );
	ula_nor g214 (.a(w152), .b(w18), .x(w57) );
	ula_not g20 (.a(w15), .x(BlueD) );
	ula_not g21 (.a(w57), .x(w58) );
endmodule // dac_setup

module io (input wire nIOREQ, output wire nTape);
	wire w484;
	wire w487;
	wire w488;	
	wire w490;
	wire w508;
	wire w514;
	wire w535;
	wire w571;
	wire w580;
	wire w611;
	wire w612;
	wire w614;
	wire w646;
	wire nPortWR;
	wire nPortRD;

	// KB
	ula_nor g284 (.a(nPortRD), .b(w647), .x(w535) );
	ula_not g33 (.a(w535), .x(w536) );
	ula_nor g249 (.a(w581), .b(nPortRD), .x(w580) );
	ula_not g29 (.a(w580), .x(w582) );
	ula_nor g250 (.a(w645), .b(nPortRD), .x(w646) );
	ula_not g26 (.a(w646), .x(w644) );
	ula_nor g217 (.a(nPortRD), .b(w9), .x(w8) );
	ula_not g24 (.a(w8), .x(w6) );
	ula_nor g218 (.a(w13), .b(nPortRD), .x(w11) );
	ula_not g25 (.a(w11), .x(w10) );

	// Ear
	ula_nor g317 (.a(w513), .b(nPortRD), .x(w514) );
	ula_not g36 (.a(w514), .x(w515) );

	// 0
	ula_nor g243 (.a(w509), .b(w510), .x(w508) );
	ula_nor g244 (.a(w507), .b(nPortWR), .x(w509) );
	ula_nor g223 (.a(w7), .b(nPortWR), .x(w507) );
	ula_nor g224 (.a(w508), .b(w507), .x(w510) );

	// 1
	ula_nor g278 (.a(w610), .b(w614), .x(w612) );
	ula_nor g279 (.a(nPortWR), .b(w611), .x(w614) );
	ula_nor g255 (.a(w478), .b(nPortWR), .x(w611) );
	ula_nor g256 (.a(w612), .b(w611), .x(w610) );

	// 2
	ula_nor g311 (.a(w570), .b(w573), .x(w572) );
	ula_nor g312 (.a(nPortWR), .b(w571), .x(w573) );
	ula_nor g289 (.a(w512), .b(nPortWR), .x(w571) );
	ula_nor g290 (.a(w572), .b(w571), .x(w570) );

	// 3
	ula_nor g323 (.a(w489), .b(w488), .x(w487) );
	ula_nor g322 (.a(w608), .b(nPortWR), .x(w488) );	
	ula_nor g341 (.a(w490), .b(w487), .x(w489) );
	ula_nor g342 (.a(nPortWR), .b(w488), .x(w490) );
	ula_not g37 (.a(w487), .x(nTape) );	

	// 4
	ula_nor g381 (.a(w538), .b(nPortWR), .x(w483) );
	ula_nor g382 (.a(w483), .b(w484), .x(w537) );
	ula_nor g371 (.a(w538), .b(w537), .x(w484) );
	ula_nor g372 (.a(nPortWR), .b(w522), .x(w538) );
	ula_not g38 (.a(w484), .x(w485) );	

	ula_nor4 g622 (.a(nIOREQ), .b(w310), .c(w244), .d(w243), .x(w237) );	
	ula_not g77 (.a(w237), .x(nPortWR) );

	ula_nor4 g623 (.a(nIOREQ), .b(w310), .c(w309), .d(w243), .x(w317) );
	ula_not g80 (.a(w317), .x(nPortRD) );
endmodule // io

module contention (input wire nMREQ, input wire nIOREQ, input wire Border, input wire A14, input wire A15, input wire C0, output wire CPUCLK);
	wire w344;
	wire w345;
	wire w346;
	wire w347;
	wire w359;
	wire w360;
	wire w361;
	wire w404;
	wire w405;
	wire w411;
	wire w414;
	wire w425;
	wire w426;
	wire w448;
	wire w477;

	// GD
	ula_nor g395 (.a(w346), .b(w347), .x(w345) );
	ula_nor g396 (.a(w405), .b(nMREQ), .x(w346) );
	ula_nor g397 (.a(w346), .b(w405), .x(w344) );
	ula_nor g394 (.a(w344), .b(w345), .x(w347) );	

	// GD
	ula_nor g392 (.a(w405), .b(nIOREQ), .x(w425) );
	ula_nor g393 (.a(w405), .b(w425), .x(w448) );
	ula_nor g402 (.a(w243), .b(w448), .x(w426) );
	ula_nor g403 (.a(w426), .b(w425), .x(w243) );

	ula_not g41 (.a(A15), .x(w411) );
	ula_not g42 (.a(w405), .x(w404) );
	ula_not g43 (.a(w414), .x(w405) );
	ula_nor4 g383 (.a(w413), .b(w412), .c(w360), .d(w361), .x(w477) );
	ula_nor3 g384 (.a(w359), .b(w477), .c(w367), .x(w414) );
	ula_nor g385 (.a(w410), .b(w411), .x(w412) );
	ula_nor g386 (.a(A14), .b(w410), .x(w413) );	
	ula_nor4 g404 (.a(w426), .b(Border), .c(w404), .d(w347), .x(w362) );
	ula_nor g411 (.a(w208), .b(w253), .x(w360) );
	ula_nor5 g405 (.a(Border), .b(w404), .c(nIOREQ), .d(w360), .e(w426), .x(w359) );	
	ula_not g45 (.a(nIOREQ), .x(w410) );	
	ula_not g48 (.a(w362), .x(w361) );

	ula_not g44 (.a(w414), .x(CPUCLK) );
endmodule // contention