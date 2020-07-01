import React, { useEffect, useState } from 'react'
import { fetchGameData } from 'components/functions/api'
import { BaseCharts } from 'components/charts/BaseCharts'

const FieldChart = ({ gameId, height }) => {
  const [data, setData] = useState([])

  useEffect(() => {
    const getGameData = async () => {
      const data = await fetchGameData(gameId, 'get_field_chart')
      setData(data)
    }
    getGameData()
  }, [gameId])
  return <BaseCharts data={data} height={height} />
}

export { FieldChart }
