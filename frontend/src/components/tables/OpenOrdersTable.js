import React, { useEffect, useState } from "react";
import { Table } from "react-bootstrap";
import { MakeTable } from "components/functions/tables";
import { fetchGameData } from "components/functions/api";

const OpenOrdersTable = ({ gameId }) => {
  const [tableData, setTableData] = useState({});
  useEffect(() => {
    const getGameData = async () => {
      const data = await fetchGameData(gameId, "get_open_orders_table");
      setTableData(data);
    };
    getGameData();
  }, [gameId]);

  console.log(tableData);
  return (
    <Table striped hover>
      {tableData.data && MakeTable(tableData)}
    </Table>
  );
};

export { OpenOrdersTable };
