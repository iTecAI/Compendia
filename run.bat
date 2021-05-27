@echo off

SET CONFIG=server.cfg
uvicorn main:app --host=0.0.0.0 --port=3004 --no-access-log --use-colors --log-level debug