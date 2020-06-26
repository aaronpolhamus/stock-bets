import React from "react";
import { ResponsiveLine } from "@nivo/line";
import { dollarizer } from "components/functions/formats";
import styled from "styled-components";

const ChartWrapper = styled.div`
  width: 100%;
  height: ${(props) => props.height || "25vw"};
`;

const BaseChart = ({ lineData, colors, height }) => {
  // See here for interactive documentation: https://nivo.rocks/line/
  return (
    <ChartWrapper height={height}>
      <ResponsiveLine
        data={lineData}
        margin={{ top: 50, right: 110, bottom: 65, left: 65 }}
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
    </ChartWrapper>
  );
};

export { BaseChart };
