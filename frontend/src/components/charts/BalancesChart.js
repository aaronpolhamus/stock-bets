import React, { useEffect, useState } from "react";
import { fetchGameData } from "components/functions/api";
import { BaseChart } from "components/charts/BaseChart";

const BalancesChart = ({ gameId, height }) => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const getGameData = async () => {
      const data = await fetchGameData(gameId, "get_balances_chart");
      setData(data);
    };
    getGameData();
  }, [gameId]);
  return <BaseChart data={data} height={height} />;
};

export { BalancesChart };
