import React, { useEffect, useState } from "react";
import { ResponsiveLine } from "@nivo/line";
import { fetchGameData } from "components/functions/api";
import { dollarizer } from "components/functions/formats";

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

  // See here for interactive documentation: https://nivo.rocks/line/
  return (
    <div style={{ width: "100%", height: height || "25vw" }}>
      <ResponsiveLine
        data={lineData}
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
          tickSize: 3,
          tickPadding: 5,
          tickRotation: -45,
        }}
        axisLeft={{
          orient: "left",
          tickSize: 2,
          tickPadding: 1,
          tickRotation: 0,
          legendOffset: -40,
          format: (v) => `${dollarizer.format(v)}`,
        }}
        colors={colors}
        pointSize={0}
        useMesh={false}
        lineCol
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

export { FieldChart };
