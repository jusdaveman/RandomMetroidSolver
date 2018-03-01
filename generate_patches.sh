#!/bin/bash

(
echo "patches = {"

cd ~/RandomMetroidSolver/itemrandomizerweb/patches

for i in *.ips; do ./ips.pl $i; done

echo '"Removes_Gravity_Suit_heat_protection": {
0x06e37d: [0x01],
0x0869dd: [0x01]},
"Mother_Brain_Cutscene_Edits": {
0x148824: [0x01,0x00],
0x148848: [0x01,0x00],
0x148867: [0x01,0x00],
0x14887f: [0x01,0x00],
0x148bdb: [0x04,0x00],
0x14897d: [0x10,0x00],
0x1489af: [0x10,0x00],
0x1489e1: [0x10,0x00],
0x148a09: [0x10,0x00],
0x148a31: [0x10,0x00],
0x148a63: [0x10,0x00],
0x148a95: [0x10,0x00],
0x148b33: [0x10,0x00],
0x148dc6: [0xb0],
0x148b8d: [0x12,0x00],
0x148d74: [0x00,0x00],
0x148d86: [0x00,0x00],
0x148daf: [0x00,0x01],
0x148e51: [0x01,0x00],
0x14b93a: [0x00,0x01],
0x148eef: [0x0a,0x00],
0x148f0f: [0x60,0x00],
0x14af4e: [0x0a,0x00],
0x14af0d: [0x0a,0x00],
0x14b00d: [0x00,0x00],
0x14b132: [0x40,0x00],
0x14b16d: [0x00,0x00],
0x14b19f: [0x20,0x00],
0x14b1b2: [0x30,0x00],
0x14b20c: [0x03,0x00]},
"Suit_acquisition_animation_skip":{
0x020717: [0xea,0xea,0xea,0xea]},
"Fix_Morph_and_Missiles_Room_State":{
0x07e655: [0xea,0xea,0xea,0xf0,0x0c,0x4c,0x5f,0xe6]},
"Fix_heat_damage_speed_echoes_bug":{
0x08b629: [0x01]},
"Disable_GT_Code":{
0x15491c: [0x80]},
"Disable_Space_Time_select_in_menu":{
0x013175: [0x01]},
"Fix_Morph_Ball_Hidden_Chozo_PLMs":{
0x0268ce: [0x04],
0x026e02: [0x04]},
"Fix_Screw_Attack_selection_in_menu":{
0x0134c5: [0x0c]}
}'
) > ~/RandomMetroidSolver/itemrandomizerweb/patches.py
