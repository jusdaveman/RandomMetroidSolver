#!/bin/bash

CWD=$(dirname $0)/..
cd ${CWD}
CWD=$(pwd)

[ -f "db_params.py" ] || exit 1

SQL_DIR=${CWD}/sql
LOG_DIR=${CWD}/logs
mkdir -p ${LOG_DIR} ${SQL_DIR}

function getDBParam {
    PARAM="$1"

    sed -e "s+.*${PARAM}='\([^']*\)'.*+\1+" ${CWD}/db_params.py
}

function info {
    MSG="$*"
    echo "$(date '+%Y/%m/%d_%H:%M:%S'): ${MSG}"
}

info "Get database parameters"

host=$(getDBParam "host")
user=$(getDBParam "user")
database=$(getDBParam "database")
password=$(getDBParam "password")

info "Start loading extended stats"

for SQL in $(ls -1 ${SQL_DIR}/extStatsOut_*.sql); do
    echo "source ${SQL};" | mysql -h ${host} -u ${user} -p${password} ${database} > ${LOG_DIR}/$(basename ${SQL}).log 2>&1 &
done

wait

info "Done"
