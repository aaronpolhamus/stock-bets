import React from "react";

const renderRow = (row, headers) => {
  return headers.map((key, index) => {
    return <td>{row[key]}</td>;
  });
};

const makeRows = (tableData) => {
  return tableData.data.map((row, index) => {
    return <tr>{renderRow(row, tableData.headers)}</tr>;
  });
};

const makeHeader = (headers) => {
  return headers.map((key, index) => {
    return <th>{key}</th>;
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
