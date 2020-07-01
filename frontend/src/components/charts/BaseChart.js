import React from "react";
import { Line } from "react-chartjs-2";
import { dollarizer } from "components/functions/formats";

const BaseChart = ({ data, height }) => {
  // See here for interactive documentation: https://nivo.rocks/line/
  return (
    <Line
      data={data}
      options={{
        legend: {
          position: "right",
        },
        elements: {
          point: {
            radius: 0,
          },
        },
        scales: {
          yAxes: [
            {
              ticks: {
                callback: function (value, index, values) {
                  if (parseInt(value) >= 1000) {
                    return (
                      "$" +
                      value.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")
                    );
                  } else {
                    return "$" + value;
                  }
                },
              },
            },
          ],
        },
      }}
    />
  );
};

export { BaseChart };
