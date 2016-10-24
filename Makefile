diffTest2: runTest2
	git diff --no-index -- assembler_test_cases/Test2.mif test

diffSorter2: runSorter2
	git diff --no-index -- assembler_test_cases/Sorter2.mif test

runTest2:
	python assemble.py -i assembler_test_cases/Test2.a32

runSorter2:
	python assemble.py -i assembler_test_cases/Sorter2.a32
