import React from "react";
import { useStyles } from "../hooks/useStyles";
import board_9x9 from "../images/board_9x9.png";
import board_13x13 from "../images/board_13x13.png";
import board_19x19 from "../images/board_19x19.png";
import { Paper } from "@material-ui/core";
import { useSelector } from "react-redux";
import { BOARD, LAST_MOVE } from "../constants/StateKeys";
import Point from "./Point";
import { POINTS, SIZE } from "../constants/BoardKeys";
import clsx from "clsx";
import { GAME } from "../constants/ReducerKeys";

function Board({ myTurn, playing, endGame }) {
  const classes = useStyles();
  const { [SIZE]: size, [POINTS]: points } = useSelector(
    (state) => state[GAME][BOARD]
  );
  const lastMove = useSelector((state) => state[GAME][LAST_MOVE]);

  let board = null;
  let borderDim = null;
  let stoneHeightWidth = null;
  // board measurements in pixels
  // 9x9: 135, 210*8, 135 -> (135-210/2)/210
  // 13x13: 105, 145*12, 105 -> (105-145/2)/145
  // 19x19: 75, 100*18, 75 -> (75-100/2)/100
  switch (size) {
    case 9:
      board = board_9x9;
      borderDim = (135 - 210 / 2) / 210;
      stoneHeightWidth = "80%";
      break;
    case 13:
      board = board_13x13;
      borderDim = (105 - 145 / 2) / 145;
      stoneHeightWidth = "90%";
      break;
    case 19:
      board = board_19x19;
      borderDim = (75 - 100 / 2) / 100;
      stoneHeightWidth = "90%";
      break;
    default:
      throw new RangeError(`Unsupported board size ${size}`);
  }
  const gridTemplateStyling = `${borderDim}fr repeat(${size}, 1fr) ${borderDim}fr`;

  return (
    <Paper
      className={clsx(
        classes.BoardContainer,
        myTurn && classes.BoardContainerMyTurn
      )}
      style={{
        gridTemplateColumns: gridTemplateStyling,
        gridTemplateRows: gridTemplateStyling,
      }}
      variant="outlined"
    >
      <img src={board} alt="go board" className={classes.BoardImage} />
      {points.map((row, i) =>
        row.map((point, j) => {
          const wasLastMove =
            lastMove && lastMove[0] === i && lastMove[1] === j;
          return (
            <Point
              key={`${i},${j}`}
              {...{
                i,
                j,
                point,
                myTurn,
                playing,
                endGame,
                stoneHeightWidth,
                wasLastMove,
              }}
            />
          );
        })
      )}
    </Paper>
  );
}

export default Board;
