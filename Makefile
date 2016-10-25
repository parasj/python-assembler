diffTest2: runTest2
	git diff --no-index --minimal -- assembler_test_cases/Test2.mif Test2.mif

diffSorter2: runSorter2
	git diff --no-index --minimal -- assembler_test_cases/Sorter2.mif Sorter2.mif

runTest2:
	python assemble.py -i assembler_test_cases/Test2.a32 -o Test2.mif

runSorter2:
	python assemble.py -i assembler_test_cases/Sorter2.a32 -o Sorter2.mif
