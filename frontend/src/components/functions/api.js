import { useState, useEffect } from "react";
import axios from "axios";

const fetchGameData = async (gameId, apiEndpoint) => {
  // helper function for components whose data can be retrieved just passing a gameId
  const response = await axios.post(`/api/${apiEndpoint}`, {
    game_id: gameId,
    withCredentials: true,
  });
  return response.data;
};

const isEmpty = function (data) {
  if (typeof data === "object") {
    if (JSON.stringify(data) === "{}" || JSON.stringify(data) === "[]") {
      return true;
    } else if (!data) {
      return true;
    }
    return false;
  } else if (typeof data === "string") {
    if (!data.trim()) {
      return true;
    }
    return false;
  } else if (typeof data === "undefined") {
    return true;
  } else {
    return false;
  }
};

const usePostRequest = (url, payload) => {
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState({});

  const postUrl = async (url, payload) => {
    try {
      setLoading(true);
      const response = await axios.post(url, {
        withCredentials: true,
        data: payload,
      });
      setData(response.data);
    } catch (error) {
      setError(error);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    postUrl(url, payload);
  }, []);

  return {
    data,
    loading,
    error,
  };
};

const fetchData = async (endpoint, data) => {
  const response = await axios.post(`/api/${endpoint}`, data);
  return response.data;
};

const fetchGameInfo = async (gameId) => {
  return await fetchData("game_info", {
    game_id: gameId,
    withCredentials: true,
  });
};

export { isEmpty, usePostRequest, fetchGameData };
