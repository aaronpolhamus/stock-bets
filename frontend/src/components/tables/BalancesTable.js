import React, { useEffect, useState } from "react";
import { Table } from "react-bootstrap";
import { fetchTableData, MakeTable } from "components/functions/tables";

const BalancesTable = ({ gameId }) => {
  const [tableData, setTableData] = useState([]);

  useEffect(async () => {
    const data = await fetchTableData(gameId, "get_current_balances_table");
    setTableData(data);
  }, []);

  return (
    <Table striped bordered hover>
      {tableData.data && MakeTable(tableData)}
    </Table>
  );
};

export { BalancesTable };
