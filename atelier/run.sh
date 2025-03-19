#!/bin/bash
mkdir -p opt_res/spec1_run10
for i in {0..9}; do
	python spec1.py $i > "opt_res/spec1_run10/output_$i.txt"
done
mv res*.pkl opt_res/spec1_run10/