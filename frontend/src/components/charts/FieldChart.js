import React, { useEffect, useState } from "react";
import { fetchGameData } from "components/functions/api";
import { BaseChart } from "components/charts/BaseChart";

const FieldChart = ({ gameId, height }) => {
  const [lineData, setLineData] = useState([]);
  const [colors, setColors] = useState([]);

  useEffect(() => {
    const getGameData = async () => {
      const data = await fetchGameData(gameId, "get_field_chart");
      setLineData(data.line_data);
      setColors(data.colors);
    };
    getGameData();
  }, [gameId]);
  return <BaseChart lineData={lineData} colors={colors} height={height} />;
};

export { FieldChart };
