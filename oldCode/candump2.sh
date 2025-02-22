#!/bin/sh

#Note: This script does not work, it includes automatic conversions of sed syntax to awk syntax.

stdbuf -o0 candump -tz can0 |stdbuf -o0 sed -E 's/can0//g;s/ \(/\(/g;s/\)    /\)/g;s/   \[/\[/g;s/\]  /\]/g;s/ /_/g;s/\)/\) ------------- /g;s/\[/ \[/g;s/\]/\] /g;

/ 03C30F0F#/ {
	print "JSM_heartbeat"
	next
}
/ 0C140.00#/ {
	print "PM_heartbeat_"
	next
}
/ 02000.00#/ {
	print "Joystick_pos_"
	next
}
/ 00E#/ {
	print "Joystick_idnt"
	next
}
/ 14300.00#/ {
	print "PM_motor_curr"
	next
}
/ 0A040.00#/ {
	print "Speed_setting"
	next
}
/ 1C300.04#/ {
	print "PM_dist_count"
	next
}
/ 1C0C0.00#/ {
	print "PM_batt_lvl_%"
	next
}
/ 051#/ {
	print "JSM_prof_chg_"
	next
}
/ 050#/ {
	print "JSM_prof_info"
	next
}
/ 061.* 00#/ {
	print "JSM_mode_sel_"
	next
}
/ 061.* 40#/ {
	print "JSM_mode_susp"
	next
}
/ 060.* 30#/ {
	print "Mode_0_sel__c"
	next
}
/ 060.* 70#/ {
	print "Mode_0_susp_c"
	next
}
/ 065.* 30#/ {
	print "Mode_1_sel__c"
	next
}
/ 065.* 70#/ {
	print "Mode_1_susp_c"
	next
}
/ 066.* 30#/ {
	print "Mode_2_sel__c"
	next
}
/ 066.* 70#/ {
	print "Mode_2_susp_c"
	next
}
/ 062.* 30#/ {
	print "Mode_3_sel__c"
	next
}
/ 062.* 70#/ {
	print "Mode_3_susp_c"
	next
}
/ 060#/ {
	print "JSM_mode_info"
	next
}
/ 181C0.00#/ {
	print "Play_4_tones_"
	next
}
/ 0C18000.#/ {
	print "Chge2drive__c"
	next
}
/ 0C18050.#/ {
	print "Chge2seat___c"
	next
}
/ 0C180.0.#/ {
	print "Chge2mouse__c"
	next
}
/ 140C0001#/ {
	print "Unknown_"
	next
}
/ 0A400.0.#/ {
	print "Mouse_data___"
	next
}
/ 1C2C0.00#/ {
	print "Time_of_day"
	next
}
/ 1C240.01#/ {
	print "Device_rdy?"
	next
}
/ 0C000006#/ {
	print "PM_motor_decl"
	next
}
/ 0C000005#/ {
	print "PM_motor_stop"
	next
}
/ 0C000300#/ {
	print "JSM_interactn"
	next
}
/ 0C380500#/ {
	print "Seat_mve_info"
	next
}
/ 0C000.01#/ {
	print "Left_indicat_"
	next
}
/ 0C000.02#/ {
	print "Right_indicat"
	next
}
/ 0C000.03#/ {
	print "Hazards_indic"
	next
}
/ 0C000.04#/ {
	print "Lights_toggle"
	next
}
/ 0C040100#/ {
	print "Horn_on_"
	next
}
/ 0C040101#/ {
	print "Horn_off"
	next
}
/ 065.* 90#/ {
	print "Seat_mve_inf2"
	next
}

'
