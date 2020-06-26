import React, { useEffect, useState } from "react";
import { Table, Button } from "react-bootstrap";
import { fetchGameData } from "components/functions/api";
import { ArrowDownLeft, ArrowUpRight, Trash } from "react-feather";
import { AlignText, SmallCaps, Subtext } from "components/textComponents/Text";

import {
  RowStyled,
  CellStyled,
  CancelButton,
} from "components/tables/TableStyledComponents";

import { makeCustomHeader } from "components/functions/tables";

const OrderTypeIcon = ({ type, ...props }) => {
  switch (type) {
    case "buy":
      return <ArrowDownLeft color="var(--color-text-light-gray)" {...props} />;
    case "sell":
      return <ArrowUpRight color="#5ac763" {...props} />;
  }
};

const tableHeaders = {
  pending: [
    {
      value: "Type",
    },
    {
      value: "Symbol",
    },
    {
      value: "Quantity",
      align: "right",
    },
    {
      value: "Price",
      align: "right",
    },
    {
      value: "Time in force",
    },
    {
      value: "Date Placed",
      align: "right",
    },
  ],
  fulfilled: [
    {
      value: "Type",
    },
    {
      value: "Symbol",
    },
    {
      value: "Quantity",
      align: "right",
    },
    {
      value: "Price",
      align: "right",
    },
    {
      value: "Date Placed",
      align: "right",
    },
  ],
};

const renderRows = (rows) => {
  return rows.map((row, index) => {
    return (
      <RowStyled>
        <td>
          <OrderTypeIcon size={20} type={row["Buy/Sell"]} />
          <SmallCaps color="var(--color-text-gray)">
            {row["Order type"]}
          </SmallCaps>
        </td>
        <td>{row["Symbol"]}</td>
        <CellStyled>
          <strong>{row["Quantity"]}</strong>
        </CellStyled>
        <CellStyled>
          <strong>{row["Order price"]}</strong>
        </CellStyled>
        <td>
          <SmallCaps>{row["Time in force"]}</SmallCaps>
        </td>
        <CellStyled>
          {row["Placed on"]}
          <CancelButton />
        </CellStyled>
      </RowStyled>
    );
  });
};

const renderFulfilledRows = (rows) => {
  return rows.map((row, index) => {
    return (
      <tr>
        <td>
          <OrderTypeIcon size={18} type={row["Buy/Sell"]} />
        </td>
        <td>{row["Symbol"]}</td>
        <CellStyled>
          <strong>{row["Quantity"]}</strong>
        </CellStyled>
        <CellStyled>
          <strong>{row["Clear price"]}</strong>
          <Subtext>{row["Hypothetical % return"]}</Subtext>
        </CellStyled>
        <CellStyled>{row["Placed on"]}</CellStyled>
      </tr>
    );
  });
};

const OpenOrdersTable = ({ gameId }) => {
  const [tableData, setTableData] = useState({});
  useEffect(() => {
    const getGameData = async () => {
      const data = await fetchGameData(gameId, "get_order_details_table");
      setTableData(data);
    };
    getGameData();
  }, [gameId]);
  if (tableData.orders) {
    return (
      <>
        <Table hover>
          <thead>
            <tr>{makeCustomHeader(tableHeaders.pending)}</tr>
          </thead>
          <tbody>{renderRows(tableData.orders.pending)}</tbody>
        </Table>
        <h2>
          <SmallCaps>Fulfilled orders</SmallCaps>
        </h2>
        <Table hover>
          <thead>
            <tr>{makeCustomHeader(tableHeaders.fulfilled)}</tr>
          </thead>
          <tbody>
            {renderFulfilledRows(tableData.orders.fulfilled.slice(0).reverse())}
          </tbody>
        </Table>
      </>
    );
  }
  return null;
};

export { OpenOrdersTable };
