import React, { useEffect, useState } from "react";
import { Table } from "react-bootstrap";
import { fetchTableData, MakeTable } from "components/functions/tables";

const OpenOrdersTable = ({ gameId }) => {
  const [tableData, setTableData] = useState([]);

  useEffect(async () => {
    const data = await fetchTableData(gameId, "get_open_orders_table");
    setTableData(data);
  }, []);

  return (
    <Table striped hover>
      {tableData.data && MakeTable(tableData)}
    </Table>
  );
};

export { OpenOrdersTable };
