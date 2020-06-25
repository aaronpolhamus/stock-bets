import React, { useEffect, useState } from "react";
import { Table, Button } from "react-bootstrap";
import { AutoTable } from "components/functions/tables";
import { fetchGameData } from "components/functions/api";

const TypeIcon = ({ type }) => {
  switch (type) {
  }
};

const renderRows = (rows) => {
  return rows.map((row, index) => {
    console.log(row);
    return (
      <tr>
        <td>
          {row["Buy/Sell"]}
          <small>{row["Order type"]}</small>
        </td>

        <td>{row["Symbol"]}</td>

        <td>{row["Quantity"]}</td>

        <td>
          {row["Price"]}
          <small>{row["Price"]}</small>
        </td>

        <td>
          {row["Time in force"]}
          <small>{row["Placed on"]}</small>
        </td>

        <td>
          <Button variant="danger" size="sm">
            Cancel Order
          </Button>
        </td>
      </tr>
    );
  });
};

const OpenOrdersTable = ({ gameId }) => {
  const [tableData, setTableData] = useState({});
  useEffect(() => {
    const getGameData = async () => {
      const data = await fetchGameData(gameId, "get_open_orders_table");
      setTableData(data);
    };
    getGameData();
  }, [gameId]);

  if (tableData.data) {
    return (
      <Table hover>
        <thead>
          <tr></tr>
        </thead>
        <tbody>{renderRows(tableData.data)}</tbody>
      </Table>
    );
  }
  return null;
};

export { OpenOrdersTable };
