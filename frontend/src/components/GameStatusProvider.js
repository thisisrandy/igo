import React, { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import { CONNECTED, STATUS, TURN, YOUR_COLOR } from "../constants/StateKeys";
import { COMPLETE, ENDGAME, PLAY } from "../constants/GameStatus";
import { GAME } from "../constants/ReducerKeys";

/**
 * Wrapper to provide joinedToGame, playing, endGame, gameInProgress, and myTurn
 * to children
 */
function GameStatusProvider({ children }) {
  const {
    [CONNECTED]: connected,
    [STATUS]: status,
    [TURN]: turn,
    [YOUR_COLOR]: yourColor,
  } = useSelector((state) => state[GAME]);

  const [joinedToGame, setJoinedToGame] = useState(false);
  useEffect(() => {
    setJoinedToGame(connected && status != null);
  }, [connected, status]);

  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    setPlaying(status === PLAY);
  }, [status]);

  const [endGame, setEndGame] = useState(false);
  useEffect(() => {
    setEndGame(status === ENDGAME);
  }, [status]);

  const [gameInProgress, setGameInProgress] = useState(false);
  useEffect(() => {
    setGameInProgress(status != null && status !== COMPLETE);
  }, [status]);

  const [myTurn, setMyTurn] = useState(false);
  useEffect(() => {
    setMyTurn(turn != null && turn === yourColor);
  }, [turn, yourColor]);

  return (
    <React.Fragment>
      {React.Children.map(children, (child) =>
        React.cloneElement(child, {
          joinedToGame,
          playing,
          endGame,
          gameInProgress,
          myTurn,
        })
      )}
    </React.Fragment>
  );
}

export default GameStatusProvider;
