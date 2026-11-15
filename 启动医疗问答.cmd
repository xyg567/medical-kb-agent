@echo off
title 医疗图谱问答 一键启动
rem 双击即可：Neo4j 没开就开、问答服务没开就开，然后自动打开浏览器
rem 数据在 env\kg 学长包 Neo4j 4.4.48 里(44112 节点/467930 关系)

set JAVA_HOME=D:\medproject\env\kg\jre\jdk-11.0.33+10-jre
set TMP=D:\medproject\env\tmp
set TEMP=D:\medproject\env\tmp
set PY=D:\medproject\ref\QASystemOnMedicalKG\.venv\Scripts\python.exe
set WEB_PY=D:\medproject\ref\QASystemOnMedicalKG\web.py
set NEO4J=D:\medproject\env\kg\neo4j\neo4j-community-4.4.48\bin\neo4j.bat

echo [1/3] 检查 Neo4j 数据库...
netstat -ano | findstr ":7474" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 goto neo_ok
echo   没在运行，正在启动，首次约 10 到 20 秒，最小化窗口请勿关闭
start "Neo4j" /min "%NEO4J%" console
ping -n 16 127.0.0.1 >nul
:neo_ok
echo   Neo4j OK

echo [2/3] 检查医疗问答服务...
netstat -ano | findstr ":5000" | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 goto web_ok
echo   没在运行，正在启动
start "医疗问答服务" /min "%PY%" "%WEB_PY%"
ping -n 10 127.0.0.1 >nul
:web_ok
echo   问答服务 OK

echo [3/3] 打开浏览器...
start "" "http://127.0.0.1:5000"
echo 完成。本窗口稍后自动关闭，最小化的两个后台窗口请保留。
ping -n 7 127.0.0.1 >nul