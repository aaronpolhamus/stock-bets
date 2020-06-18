import React, { useEffect, useState } from "react";
import { Table } from "react-bootstrap";
import { MakeTable } from "components/functions/tables";
import { fetchGameData } from "components/functions/api";

const PayoutsTable = ({ gameId }) => {
  const [tableData, setTableData] = useState({});
  useEffect(() => {
    const getGameData = async () => {
      const data = await fetchGameData(gameId, "get_payouts_table");
      setTableData(data);
    };
    getGameData();
  }, [gameId]);
  return <Table hover>{tableData.data && MakeTable(tableData)}</Table>;
};

export { PayoutsTable };