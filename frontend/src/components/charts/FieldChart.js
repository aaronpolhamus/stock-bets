import React, { useEffect, useState } from "react";
import axios from "axios";
import { ResponsiveLine } from '@nivo/line'
import { Card } from "react-bootstrap";

const fetchChartData = async (gameId) => { 
  const response = await axios.post("/api/field_chart", { game_id: gameId, withCredentials: true })
  console.log(response)
  return response.data
}

const FieldChart = ({ gameId }) => {
  const [chartData, setChartData] = useState([])  

  useEffect(async () => {
    const data = await fetchChartData(gameId)
    setChartData(data) 
  }, [])

  // See here for interactive documentation: https://nivo.rocks/line/
  return (
    <Card style={{ width: '75vw', height: '25vw' }}>
      <Card.Title>The field</Card.Title>
      <ResponsiveLine
          data={chartData}
          margin={{ top: 50, right: 110, bottom: 50, left: 60 }}
          xScale={{ type: 'point'}}
          yScale={{ type: 'linear', min: 'auto', max: 'auto', stacked: false, reverse: false }}
          curve="natural"
          axisTop={null}
          axisRight={null}
          axisBottom={{
              orient: 'bottom',
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              legend: 'Time index',
              legendOffset: 36,
              legendPosition: 'middle',
              tickValues: 20
          }}
          axisLeft={{
              orient: 'left',
              tickSize: 5,
              tickPadding: 5,
              tickRotation: 0,
              legend: 'Position value',
              legendOffset: -40,
              legendPosition: 'middle'
          }}
          colors={{ scheme: 'nivo' }}
          pointSize={0}
          useMesh={false}
          legends={[
              {
                  anchor: 'bottom-right',
                  direction: 'column',
                  justify: false,
                  translateX: 100,
                  translateY: 0,
                  itemsSpacing: 0,
                  itemDirection: 'left-to-right',
                  itemWidth: 80,
                  itemHeight: 20,
                  itemOpacity: 0.75,
                  symbolSize: 12,
                  symbolShape: 'circle',
                  symbolBorderColor: 'rgba(0, 0, 0, .5)',
                  effects: [
                      {
                          on: 'hover',
                          style: {
                              itemBackground: 'rgba(0, 0, 0, .03)',
                              itemOpacity: 1
                          }
                      }
                  ]
              }
          ]}
      />
    </Card>
  )
};
 
export {FieldChart};

