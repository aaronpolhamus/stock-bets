import React, { useEffect, useState } from "react";
import { Table } from "react-bootstrap";
import { MakeTable } from "components/functions/tables";
import { fetchGameData } from "components/functions/api";

const BalancesTable = ({ gameId }) => {
  const [tableData, setTableData] = useState([]);

  useEffect(async () => {
    const data = await fetchGameData(gameId, "get_current_balances_table");
    setTableData(data);
  }, []);

  return <Table hover>{tableData.data && MakeTable(tableData)}</Table>;
};

export { BalancesTable };
