#!/bin/sh

#A simple sed script that prints all received CAN frames and puts readable
#labels on the ones that are already known. You can add or remove ";d"
#before the last closing brace in every of the lines below to show/hide
#the matching frames, making it easier to focus on unknown ones.

stdbuf -o0 candump -tz can0 |stdbuf -o0 sed -E 's/can0//g;s/ \(/\(/g;s/\)    /\)/g;s/   \[/\[/g;s/\]  /\]/g;s/ /_/g;s/\)/\) ------------- /g;s/\[/ \[/g;s/\]/\] /g;

/03C30F0F/{s/ -* / JSM_heartbeat /g;d};
/0C140.00/{s/ -* / PM_heartbeat_ /g;d};
/02000.00/{s/ -* / Joystick_pos_ /g;d};
/_____00E/{s/ -* / Joystick_idnt /g;d};
/14300.00/{s/ -* / PM_motor_curr /g;d};
/0A040.00/{s/ -* / Speed_setting /g};
/1C300.04/{s/ -* / PM_dist_count /g;d};
/1C0C0.00/{s/ -* / PM_batt_lvl_% /g;d};
/_____051/{s/ -* / JSM_prof_chg_ /g};
/_____050/{s/ -* / JSM_prof_info /g};
/_____061.* 00/{s/ -* / JSM_mode_sel_ /g};
/_____061.* 40/{s/ -* / JSM_mode_susp /g};
/_____060.* 30/{s/ -* / Mode_0_sel__c /g};
/_____060.* 70/{s/ -* / Mode_0_susp_c /g};
/_____065.* 30/{s/ -* / Mode_1_sel__c /g};
/_____065.* 70/{s/ -* / Mode_1_susp_c /g};
/_____066.* 30/{s/ -* / Mode_2_sel__c /g};
/_____066.* 70/{s/ -* / Mode_2_susp_c /g};
/_____062.* 30/{s/ -* / Mode_3_sel__c /g};
/_____062.* 70/{s/ -* / Mode_3_susp_c /g};
/_____060/{s/ -* / JSM_mode_info /g};
/181C0.00/{s/ -* / Play_4_tones_ /g;d};
/0C18000./{s/ -* / Chge2drive__c /g};
/0C18050./{s/ -* / Chge2seat___c /g};
/0C180.0./{s/ -* / Chge2mouse__c /g};
/140C0001/{s/ -* / Unknown______ /g;d};
/0C380400/{s/ -* / Unknown_SOMET /g;d};
/0A400.0./{s/ -* / Mouse_data___ /g;d};
/1C2C0.00/{s/ -* / Time_of_day /g;d};
/1C240.01/{s/ -* / Device_rdy? /g;d};
/0C000006/{s/ -* / PM_motor_decl /g};
/0C000005/{s/ -* / PM_motor_stop /g};
/0C000300/{s/ -* / JSM_interactn /g;d};
/0C380500/{s/ -* / Seat_mve_info /g;d};
/0C000.01/{s/ -* / Left_indicat_ /g};
/0C000.02/{s/ -* / Right_indicat /g};
/0C000.03/{s/ -* / Hazards_indic /g};
/0C000.04/{s/ -* / Lights_toggle /g};
/0C040100/{s/ -* / Horn_on______ /g};
/0C040101/{s/ -* / Horn_off_____ /g};
/_____065.* 90/{s/ -* / Seat_mve_inf2 /g};

'
