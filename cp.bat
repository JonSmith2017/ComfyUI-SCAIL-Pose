@echo off
for /R .  %%i  IN (*.java *.cpp *.xml *.c )  do (
echo %%i
cat %%i > %%i.txt
mv %%i.txt %%i
)

