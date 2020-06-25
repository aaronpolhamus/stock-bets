import React, { useEffect, useState } from "react";
import { Table } from "react-bootstrap";
import { AutoTable } from "components/functions/tables";
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

  return <AutoTable hover tableData={tableData} />;
};

export { OpenOrdersTable };
