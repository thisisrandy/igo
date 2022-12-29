import React from "react";
import { useStyles } from "../hooks/useStyles";
import blackStone from "../images/black.png";
import whiteStone from "../images/white.png";
import { useDispatch, useSelector } from "react-redux";
import { send } from "@giantmachines/redux-websocket";
import {
  ACTION_TYPE,
  COORDS,
  KEY,
  TYPE,
} from "../constants/OutgoingMessageKeys";
import { GAME_ACTION } from "../constants/OutgoingMessageTypes";
import { MARK_DEAD, PLACE_STONE } from "../constants/GameActionTypes";
import { CONNECTED, KEYS, YOUR_COLOR } from "../constants/StateKeys";
import clsx from "clsx";
import ClearIcon from "@material-ui/icons/Clear";
import { BLACK, WHITE } from "../constants/Colors";
import { GAME } from "../constants/ReducerKeys";

function Point({
  i,
  j,
  point,
  myTurn,
  playing,
  endGame,
  stoneHeightWidth,
  wasLastMove,
}) {
  const classes = useStyles();
  const {
    [YOUR_COLOR]: yourColor,
    [KEYS]: keys,
    [CONNECTED]: connected,
  } = useSelector((state) => state[GAME]);
  const dispatch = useDispatch();

  const emptyPointClickHandler = (i, j) => () => {
    if (connected && playing && myTurn) {
      dispatch(
        send({
          [TYPE]: GAME_ACTION,
          [KEY]: keys[yourColor],
          [ACTION_TYPE]: PLACE_STONE,
          [COORDS]: [i, j],
        })
      );
    }
  };

  const stoneClickHandler = (i, j) => () => {
    if (connected && endGame) {
      dispatch(
        send({
          [TYPE]: GAME_ACTION,
          [KEY]: keys[yourColor],
          [ACTION_TYPE]: MARK_DEAD,
          [COORDS]: [i, j],
        })
      );
    }
  };

  const clickable = (!point[0] && playing && myTurn) || (point[0] && endGame);

  // NOTE: point is an array of length 4 with contents as follows:
  // [
  //    stone in ("w", "b", ""),
  //    marked dead in (true, false),
  //    counted in (true, false),
  //    counted for in ("w", "b", "")
  // ]

  return (
    <React.Fragment>
      {/* the images are wrapped in a div for compatibility with some older
      devices. see https://stackoverflow.com/a/67527395/12162258 */}
      <div
        className={clsx(classes.ImageCell, wasLastMove && classes.LastMove)}
        style={{
          gridRow: i + 2,
          gridColumn: j + 2,
        }}
      >
        {point[0] && (
          <img
            src={point[0] === "w" ? whiteStone : blackStone}
            alt={`${point[0] === "w" ? WHITE : BLACK} stone`}
            className={classes.StoneImage}
            style={{
              height: stoneHeightWidth,
              width: stoneHeightWidth,
            }}
          />
        )}
        {point[1] && (
          <ClearIcon
            style={{ height: stoneHeightWidth, width: stoneHeightWidth }}
            className={classes.DeadStone}
            aria-label={`${
              point[0] === "w" ? WHITE : BLACK
            } stone marked as dead awaiting response at coordinates (${i}, ${j})`}
          />
        )}
      </div>
      <div
        className={clsx(
          classes.Point,
          clickable && classes.PointHover,
          point[2] && point[3] === "w" && classes.CountedWhite,
          point[2] && point[3] === "b" && classes.CountedBlack
        )}
        style={{ gridRow: i + 2, gridColumn: j + 2 }}
        onClick={
          !point[0] ? emptyPointClickHandler(i, j) : stoneClickHandler(i, j)
        }
        aria-label={`${clickable ? "" : "un"}clickable ${
          point[0] ? `${point[0] === "w" ? WHITE : BLACK} stone` : "point"
        }${
          point[2]
            ? ` counted for ${
                point[3] === "w" ? WHITE : point[3] === "b" ? BLACK : "no one"
              }`
            : ""
        } at coordinates (${i}, ${j})${
          playing && wasLastMove ? ", which was the last move" : ""
        }`}
        role="button"
      />
    </React.Fragment>
  );
}

export default Point;
