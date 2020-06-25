import React from "react";

const renderRow = (row, headers, exclude = ["order_id"]) => {
  return headers.map((key, index) => {
    if (exclude.includes(key)) {
      return null;
    }
    return <td key={index}>{row[key]}</td>;
  });
};

const makeRows = (tableData, exclude = ["order_id"]) => {
  // The exclude option allows us to leave out data that we don't necessarily want represented in our table, e.g. the
  // order id for order cancellations
  return tableData.data.map((row, index) => {
    return <tr key={index}>{renderRow(row, tableData.headers, exclude)}</tr>;
  });
};

const makeHeader = (headers) => {
  return headers.map((key, index) => {
    return <th key={key}>{key}</th>;
  });
};

const MakeTable = (tableData) => {
  return (
    <>
      <thead>
        <tr>{makeHeader(tableData.headers)}</tr>
      </thead>
      <tbody>{makeRows(tableData)}</tbody>
    </>
  );
};

export { MakeTable };
