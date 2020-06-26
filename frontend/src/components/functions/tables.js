import React from "react";
import { Table } from "react-bootstrap";

const renderRow = (row, headers) => {
  return headers.map((key, index) => {
    return <td key={index}>{row[key]}</td>;
  });
};

const makeRows = (tableData) => {
  return tableData.data.map((row, index) => {
    return <tr key={index}>{renderRow(row, tableData.headers)}</tr>;
  });
};

const makeHeader = (headers) => {
  return headers.map((key, index) => {
    return <th key={key}>{key}</th>;
  });
};

const AutoTable = (props) => {
  if (props.tabledata.data) {
    return (
      <Table {...props}>
        <thead>
          <tr>{makeHeader(props.tabledata.headers)}</tr>
        </thead>
        <tbody>{makeRows(props.tabledata)}</tbody>
      </Table>
    );
  }
  return null;
};

export { AutoTable, makeHeader, makeRows };
