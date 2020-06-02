import React from "react";
import axios from "axios";

const fetchTableData = async (gameId, apiEndpoint) => {
  const response = await axios.post(`/api/${apiEndpoint}`, {
    game_id: gameId,
    withCredentials: true,
  });
  return response.data;
};

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

export { fetchTableData, MakeTable };
