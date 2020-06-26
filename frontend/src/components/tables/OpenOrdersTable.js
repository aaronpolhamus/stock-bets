import React, { useEffect, useState } from "react";
import { Table, Button } from "react-bootstrap";
import { fetchGameData } from "components/functions/api";
import { ArrowDownLeft, ArrowUpRight, Trash } from "react-feather";
import {
  OnHoverToggle,
  AlignText,
  CustomTr,
  SmallCaps,
  Subtext,
} from "components/textComponents/Text";

import { makeHeader } from "components/functions/tables";

const OrderTypeIcon = ({ type, ...props }) => {
  switch (type) {
    case "buy":
      return <ArrowDownLeft color="var(--color-success)" {...props} />;
    case "sell":
      return <ArrowUpRight color="var(--color-text-gray)" {...props} />;
  }
};

const customHeaders = [
  "Type",
  "Symbol",
  "Quantity",
  "Price",
  "Time in force",
  "Date Placed",
];

const renderRows = (rows) => {
  return rows.map((row, index) => {
    return (
      <CustomTr>
        <td>
          <OrderTypeIcon size={18} type={row["Buy/Sell"]} />
          <SmallCaps color="var(--color-text-gray)">
            {row["Order type"]}
          </SmallCaps>
        </td>
        <td>{row["Symbol"]}</td>
        <td>
          <strong>{row["Quantity"]}</strong>
        </td>
        <td>
          <strong>{row["Price"]}</strong>
          <Subtext>{row["Price"]}</Subtext>
        </td>
        <td>
          <SmallCaps>{row["Time in force"]}</SmallCaps>
        </td>
        <td>
          {row["Placed on"]}
          <button>
            <Trash size={14} />
          </button>
        </td>
      </CustomTr>
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
          <tr>{makeHeader(customHeaders)}</tr>
        </thead>
        <tbody>{renderRows(tableData.data)}</tbody>
      </Table>
    );
  }
  return null;
};

export { OpenOrdersTable };
