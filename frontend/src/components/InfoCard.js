import React, { useCallback } from "react";
import Clock from "./Clock";
import { Paper, Typography } from "@material-ui/core";
import { useStyles } from "../hooks/useStyles";
import { useSelector } from "react-redux";
import { STATUS, RESULT } from "../constants/StateKeys";
import * as statusTypes from "../constants/GameStatus";
import * as resultTypes from "../constants/ResultType";
import { RESULT_TYPE, WINNER } from "../constants/ResultKeys";
import { BLACK, WHITE } from "../constants/Colors";
import { capitalizeFirstLetter } from "../utils";
import { GAME } from "../constants/ReducerKeys";

function InfoCard() {
  const classes = useStyles();
  const { [STATUS]: gameStatus, [RESULT]: gameResult } = useSelector(
    (state) => state[GAME]
  );

  const prettyStatus = useCallback(() => {
    if (gameStatus == null) return "-";
    switch (gameStatus) {
      case statusTypes.PLAY:
        return "In play";
      case statusTypes.ENDGAME:
        return "Endgame";
      case statusTypes.COMPLETE:
        return "Complete";
      case statusTypes.REQUEST_PENDING:
        return "Request pending";
      default:
        throw new TypeError(`Unknown game status ${gameStatus} encountered`);
    }
  }, [gameStatus]);

  const prettyResult = useCallback(() => {
    if (gameResult == null) return "-";
    switch (gameResult[RESULT_TYPE]) {
      case resultTypes.DRAW:
        return "Draw";
      case resultTypes.RESIGNATION:
        return `${capitalizeFirstLetter(
          gameResult[WINNER] === WHITE ? BLACK : WHITE
        )} resigned`;
      case resultTypes.STANDARD_WIN:
        return `${capitalizeFirstLetter(gameResult[WINNER])} won`;
      default:
        throw new TypeError(
          `Unknown game result type ${gameResult[RESULT_TYPE]} encountered`
        );
    }
  }, [gameResult]);

  return (
    <Paper className={classes.InfoCard}>
      <Paper className={classes.InfoCardChild}>
        <Typography>Game status: {prettyStatus()}</Typography>
      </Paper>
      <Clock />
      <Paper className={classes.InfoCardChild}>
        <Typography>Result: {prettyResult()}</Typography>
      </Paper>
    </Paper>
  );
}

export default InfoCard;
