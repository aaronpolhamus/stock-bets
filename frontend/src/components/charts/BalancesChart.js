import React, { useEffect, useState } from "react";
import { ResponsiveLine } from "@nivo/line";
import { fetchGameData } from "components/functions/api";

const BalancesChart = ({ gameId }) => {
  const [chartData, setChartData] = useState([]);
  useEffect(() => {
    const getGameData = async () => {
      const data = await fetchGameData(gameId, "get_balances_chart");
      setChartData(data);
    };
    getGameData();
  }, [gameId]);

  // backend generates all info -> point
  // frontend generates missing info -> time

  // See here for interactive documentation: https://nivo.rocks/line/
  return (
    <div style={{ width: "100%", height: "25vw" }}>
      <ResponsiveLine
        data={chartData}
        margin={{ top: 50, right: 110, bottom: 50, left: 60 }}
        xScale={{ type: "point" }}
        yScale={{
          type: "linear",
          min: "auto",
          max: "auto",
          stacked: false,
          reverse: false,
        }}
        curve="natural"
        axisTop={null}
        axisRight={null}
        axisBottom={{
          orient: "bottom",
          tickSize: 5,
          tickPadding: 5,
          tickRotation: -45,
          legendOffset: 36,
          legendPosition: "middle",
        }}
        axisLeft={{
          orient: "left",
          tickSize: 5,
          tickPadding: 5,
          tickRotation: 0,
          legendOffset: -40,
          legendPosition: "middle",
        }}
        colors={{ scheme: "nivo" }}
        pointSize={0}
        useMesh={false}
        legends={[
          {
            anchor: "bottom-right",
            direction: "column",
            justify: false,
            translateX: 100,
            translateY: 0,
            itemsSpacing: 0,
            itemDirection: "left-to-right",
            itemWidth: 80,
            itemHeight: 20,
            itemOpacity: 0.75,
            symbolSize: 12,
            symbolShape: "circle",
            symbolBorderColor: "rgba(0, 0, 0, .5)",
            effects: [
              {
                on: "hover",
                style: {
                  itemBackground: "rgba(0, 0, 0, .03)",
                  itemOpacity: 1,
                },
              },
            ],
          },
        ]}
      />
    </div>
  );
};

export { BalancesChart };
