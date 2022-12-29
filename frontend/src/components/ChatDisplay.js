import React, { useEffect, useRef, useState } from "react";
import { useSelector } from "react-redux";
import { CHAT_MESSAGES, YOUR_COLOR } from "../constants/StateKeys";
import { useStyles } from "../hooks/useStyles";
import { format, isSameDay } from "date-fns";
import { COLOR, ID, MESSAGE, TIMESTAMP } from "../constants/ChatMessageKeys";
import blackAvatar from "../images/black-avatar.png";
import whiteAvatar from "../images/white-avatar.png";
import { BLACK } from "../constants/Colors";
import { capitalizeFirstLetter, truncate } from "../utils";
import clsx from "clsx";
import {
  Button,
  IconButton,
  Snackbar,
  Typography,
  Zoom,
} from "@material-ui/core";
import CloseIcon from "@material-ui/icons/Close";
import { breakLongWords } from "../utils";
import SimpleBar from "simplebar-react";
import "simplebar/dist/simplebar.min.css";
import { GAME } from "../constants/ReducerKeys";

// NOTE: we're not dealing with a fixed-width font, so obviously the "correct"
// line width varies depending on the characters involved, but for e.g. a string
// of O's, 26 is a good length. certainly there are some cases where the dashed
// portion will appear next to its suffix, but I don't care enough to find a
// better solution. this fixes horizontal scrolling/avatar squashing, which is
// the main point
const formatMessage = (text) => breakLongWords(text, 26);
const snackBarDuration = 5000;
const snackBarMaxTextLength = 20;

function ChatDisplay({ focusInput }) {
  const classes = useStyles();
  const { [CHAT_MESSAGES]: chatMessages, [YOUR_COLOR]: yourColor } =
    useSelector((state) => state[GAME]);

  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMsg, setSnackbarMsg] = useState("");
  const [prevMsgId, setPrevMsgId] = useState(null);
  const handleClose = () => {
    setSnackbarOpen(false);
  };
  useEffect(() => {
    // we display a snackbar iff there are any messages and the last one has the
    // following properties: we haven't seen it before in this session, it is
    // from the other player, and it was recently sent
    //
    // NOTE: [] is not falsey, despite the fact that [] == false (see
    // https://stackoverflow.com/a/33567406/12162258 for why), so we have to
    // explicitly check length
    if (chatMessages && chatMessages.length) {
      const {
        [ID]: id,
        [TIMESTAMP]: timestamp,
        [COLOR]: color,
        [MESSAGE]: message,
      } = chatMessages[chatMessages.length - 1];
      if (id !== prevMsgId) {
        setPrevMsgId(id);
        if (
          color !== yourColor &&
          // note that server time is in seconds and javascript time is
          // millseconds. note also that this breaks if client and server time
          // are far out of sync, but that seems unlikely on any modern auto
          // internet time syncing device
          Date.now() - timestamp * 1000 <= snackBarDuration
        ) {
          setSnackbarMsg(
            `${capitalizeFirstLetter(color)} says: ${truncate(
              message,
              snackBarMaxTextLength
            )}`
          );
          setSnackbarOpen(true);
        }
      }
    }
  }, [chatMessages, prevMsgId, yourColor]);

  return (
    <React.Fragment>
      <Snackbar
        anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
        open={snackbarOpen}
        autoHideDuration={snackBarDuration}
        onClose={handleClose}
        message={snackbarMsg}
        action={
          <React.Fragment>
            <Button
              color="secondary"
              size="small"
              onClick={() => {
                handleClose();
                focusInput();
              }}
            >
              Reply
            </Button>
            <IconButton
              size="small"
              aria-label="close"
              color="inherit"
              onClick={handleClose}
            >
              <CloseIcon fontSize="small" />
            </IconButton>
          </React.Fragment>
        }
        TransitionComponent={Zoom}
      />
      <ChatScroller className={classes.ChatMessages}>
        {chatMessages &&
          chatMessages.map((message, index) => {
            const previous = chatMessages[index - 1];
            const showDay = shouldShowDay(previous, message);

            return shouldShowAvatar(previous, message) ? (
              <FirstMessageFromUser
                key={message[ID]}
                {...{ message, showDay, classes }}
              />
            ) : (
              <SubsequentMessage key={message[ID]} {...{ message, classes }} />
            );
          })}
      </ChatScroller>
    </React.Fragment>
  );
}

function SubsequentMessage({ message, classes }) {
  return (
    <div>
      <div className={clsx(classes.ChatMessage, classes.ChatMessageNoAvatar)}>
        <Typography variant="body2">
          {formatMessage(message[MESSAGE])}
        </Typography>
      </div>
    </div>
  );
}

function FirstMessageFromUser({ message, showDay, classes }) {
  const author = message[COLOR];

  return (
    <div>
      {showDay && (
        <div className={classes.Day}>
          <div className={classes.DayLine} />
          <Typography className={classes.DayText}>
            {format(message[TIMESTAMP] * 1000, "PP")}
          </Typography>
          <div className={classes.DayLine} />
        </div>
      )}
      <div className={clsx(classes.ChatMessage, classes.ChatMessageWithAvatar)}>
        <div
          className={classes.Avatar}
          style={{
            backgroundImage: `url(${
              author === BLACK ? blackAvatar : whiteAvatar
            })`,
          }}
        />
        <div className={classes.Author}>
          <div style={{ display: "flex", alignItems: "flex-end" }}>
            <Typography className={classes.UserName}>
              {capitalizeFirstLetter(author)}{" "}
            </Typography>
            <Typography className={classes.TimeStamp}>
              {format(message[TIMESTAMP] * 1000, "h:mm a")}
            </Typography>
          </div>
          <Typography variant="body2">
            {formatMessage(message[MESSAGE])}
          </Typography>
        </div>
      </div>
    </div>
  );
}

function shouldShowAvatar(previous, message) {
  // is this the first message of the game?
  if (!previous) return true;

  // is this message written by a different user than the previous one?
  if (previous[COLOR] !== message[COLOR]) return true;

  // has it been longer than five minutes?
  return message[TIMESTAMP] - previous[TIMESTAMP] > 300;
}

function shouldShowDay(previous, message) {
  // is this the first message of the game?
  if (!previous) return true;

  // otherwise only show when the day changes
  return !isSameDay(previous[TIMESTAMP] * 1000, message[TIMESTAMP] * 1000);
}

function ChatScroller(props) {
  // use ref to access the DOM node for the returned div below. we can then
  // check whenever the box is scrolled if it is at the bottom. if so, when the
  // component rerenders, we can auto-scroll to the bottom, and if not, we stay
  // where we are
  const ref = useRef();
  const shouldScrollRef = useRef(true);

  useEffect(() => {
    if (shouldScrollRef.current) {
      const node = ref.current;
      node.scrollTop = node.scrollHeight;
    }
  });

  const handleScroll = () => {
    const node = ref.current;
    const { clientHeight, scrollTop, scrollHeight } = node;
    shouldScrollRef.current = clientHeight + scrollTop === scrollHeight;
  };

  // FIXME: simple bar creates a double scrollbar on iOS. all attempts to fix
  // this thus far have failed. it may be that a css only option is the best.
  // see https://css-tricks.com/the-current-state-of-styling-scrollbars/ for
  // options
  //
  // A bug has been filed against simplebar here:
  // https://github.com/Grsmto/simplebar/issues/568
  return (
    <SimpleBar
      {...props}
      scrollableNodeProps={{ ref: ref, onScroll: handleScroll }}
    />
  );
}

export default ChatDisplay;
