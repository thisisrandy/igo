import { grey, red } from "@material-ui/core/colors";
import { makeStyles } from "@material-ui/core/styles";

const useStyles = makeStyles(
  (theme) => ({
    App: {
      display: "flex",
      flexDirection: "row",
      flexWrap: "wrap",
      justifyContent: "center",
    },
    TopDrawer: {
      width: "auto",
    },
    TopBarButton: {
      marginRight: theme.spacing(2),
    },
    TopBarTitle: {
      flexGrow: 1,
    },
    AlertProgressContainer: {
      display: "flex",
      justifyContent: "center",
      paddingBottom: 6,
    },
    AlertProgress: {
      marginBottom: 10,
    },
    MessageButtonContainer: {
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
    },
    DialogButtonContainer: {
      display: "flex",
      alignItems: "center",
      justifyContent: "flex-end",
    },
    StatusControlsContainer: {
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
    },
    BoardContainer: {
      [theme.breakpoints.down(850)]: {
        padding: 5,
        margin: 10,
        height: "95vw",
        width: "95vw",
      },
      [theme.breakpoints.up(850)]: {
        padding: 10,
        margin: 20,
        height: 800,
        width: 800,
      },
      display: "grid",
      justifyItems: "center",
      alignItems: "center",
      borderColor: theme.palette.grey[700],
      borderWidth: 3,
    },
    BoardContainerMyTurn: {
      borderColor: theme.palette.primary.main,
    },
    BoardImage: {
      gridColumn: "1 / -1",
      gridRow: "1 / -1",
      display: "block",
      height: "100%",
      width: "100%",
    },
    ImageCell: {
      height: "100%",
      width: "100%",
      position: "relative",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
    },
    StoneImage: {
      position: "absolute",
      zIndex: 1,
    },
    Point: {
      height: "100%",
      width: "100%",
      zIndex: 2,
    },
    PointHover: {
      "&:hover": {
        backgroundColor: "rgba(0, 0, 0, 0.4)",
        cursor: "pointer",
      },
    },
    DeadStone: {
      position: "absolute",
      color: red[400],
      zIndex: 3,
    },
    CountedWhite: {
      backgroundColor: "rgba(255, 255, 255, 0.4)",
    },
    CountedBlack: {
      backgroundColor: "rgba(0, 0, 0, 0.4)",
    },
    LastMove: {
      backgroundColor: "rgba(0, 0, 0, 0.3)",
    },
    GameControlsContainer: {
      padding: 10,
      [theme.breakpoints.down(850)]: {
        margin: 10,
        width: "80vw",
        flexWrap: "wrap",
      },
      [theme.breakpoints.up(850)]: {
        margin: 20,
        width: 750,
      },
      minWidth: 350,
      display: "flex",
      flexDirection: "row",
      justifyContent: "space-evenly",
    },
    Button: {
      margin: "8px 20px",
      minWidth: 110,
    },
    DialogContent: {
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
    },
    FormContainer: {
      display: "flex",
      flexDirection: "column",
    },
    BoardSizeSelectContainer: {
      width: "100%",
      display: "flex",
      justifyContent: "center",
    },
    BoardSizeSelect: {
      width: "50%",
    },
    KomiTextContainer: {
      width: "100%",
      display: "flex",
      justifyContent: "center",
    },
    KomiTextField: {
      width: "50%",
    },
    JoinResumeInput: {
      [theme.breakpoints.down(450)]: {
        width: 250,
      },
      [theme.breakpoints.up(450)]: {
        width: 300,
      },
    },
    JoinResumeDropdownItemContainer: {
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
    },
    CentralContainer: {
      display: "flex",
      flexWrap: "wrap",
      justifyContent: "center",
    },
    CentralSubContainer: {
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
    },
    // all of the chat styling is super fragile, and I hate it, but I don't know
    // how else to keep ChatDisplay from growing the box once the chat thread
    // gets longer than the initial height can fit, so we have to specify exact
    // heights at all the responsive breakpoints. everything here goes to shit
    // if margins/breakpoints/sizes/anything elsewhere get changed, so be
    // warned.
    //
    // explanation of the numbers:
    // 755: the point >= to which chat and player cards are side-by-side. flex
    // wrap kicks in below this point
    // 482: the size of two stacked player cards with larger (20px) margins
    // separating them
    // 462: the size of two player cards with small (10px) margins
    ChatCard: {
      width: 350,
      minHeight: 350,
      [theme.breakpoints.down(755)]: {
        maxHeight: 350,
      },
      [theme.breakpoints.up(755)]: {
        maxHeight: 462,
      },
      [theme.breakpoints.down(850)]: {
        margin: 10,
      },
      [theme.breakpoints.up(850)]: {
        margin: "20px 10px",
        maxHeight: 482,
      },
      display: "flex",
      flexDirection: "column",
    },
    ChatDisplayContainer: {
      display: "flex",
      flexGrow: 1,
      overflow: "hidden",
      // broken on old iPhone, of course. maxHeight fixes at the expense of
      // robustness. 160 is the height of the chat display in a card of height
      // 350 with input and header considered
      [theme.breakpoints.down(755)]: {
        maxHeight: 160,
      },
      // also broken on old iPad. 272 is the chat display height with small
      // margins
      [theme.breakpoints.up(755)]: {
        maxHeight: 272,
      },
      // and 292 is height with large margins. probably this isn't necessary,
      // but might as well lock everything in exactly in case there are other
      // affected devices
      [theme.breakpoints.up(850)]: {
        maxHeight: 292,
      },
      paddingTop: 0,
      paddingBottom: 0,
    },
    ChatCardActions: {
      padding: 16,
    },
    ChatMessages: {
      flex: 1,
      borderStyle: "solid",
      border: 1,
      borderRadius: theme.spacing(0.5),
      borderColor: grey[500],
      padding: "0px 10px",
    },
    ChatMessage: {
      margin: "5px 0",
      display: "flex",
    },
    ChatMessageNoAvatar: {
      marginLeft: 38,
    },
    ChatMessageWithAvatar: {
      display: "flex",
      marginTop: 10,
    },
    Avatar: {
      width: 30,
      // for some reason multi-line messages squash the avatar. adding minWidth
      // prevents this from happening
      minWidth: 30,
      height: 30,
      borderRadius: 3,
      backgroundSize: "cover",
      backgroundPosition: "center center",
    },
    Author: {
      marginLeft: 8,
    },
    UserName: {
      fontWeight: "bold",
      fontSize: "90%",
      paddingRight: 4,
    },
    TimeStamp: {
      color: "#999",
      fontSize: "80%",
    },
    Day: {
      display: "flex",
      alignItems: "center",
    },
    DayLine: {
      flex: 1,
      height: 1,
      background: "#ccc",
    },
    DayText: {
      fontWeight: "bold",
      padding: 10,
      fontSize: "80%",
    },
    ChatInput: {
      flexGrow: 1,
    },
    ChatButton: {
      marginLeft: 16,
    },
    PlayerCardContainer: {
      minWidth: 350,
      [theme.breakpoints.down(850)]: {
        margin: 10,
      },
      [theme.breakpoints.up(850)]: {
        margin: "20px 10px",
      },
      padding: 10,
      borderWidth: 3,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
    },
    PlayerCardSelf: {
      borderColor: theme.palette.primary.main,
    },
    PlayerCardNeutral: {
      borderColor: theme.palette.grey[700],
    },
    PlayerCardOpponentNotConnected: {
      borderColor: red[400],
    },
    PlayerCardSpan: {
      width: "100%",
      display: "flex",
      flexDirection: "row",
      justifyContent: "space-around",
    },
    PlayerCardSubContainer: {
      margin: 10,
      padding: 10,
      display: "flex",
    },
    PlayerCardScoreColumn: {
      padding: 5,
      display: "flex",
      flexDirection: "column",
      justifyContent: "space-around",
    },
    PlayerStoneImage: {
      height: 100,
      width: "auto",
    },
    PlayerCardKeyContainer: {
      margin: "0px 10px 10px",
      padding: 10,
      display: "flex",
      alignItems: "center",
      minHeight: 45,
    },
    InfoCard: {
      display: "flex",
      justifyContent: "space-evenly",
      [theme.breakpoints.down(850)]: {
        margin: 10,
        width: "80vw",
        flexWrap: "wrap",
      },
      [theme.breakpoints.up(850)]: {
        margin: 20,
      },
      minWidth: 350,
    },
    InfoCardChild: {
      margin: 10,
      padding: "10px 30px",
    },
  }),
  // without this, MUI styles override user-specified styles in some cases.
  // supposedly import order is the real culprit (makeStyles must be called
  // after MUI imports), but changing that didn't make a difference. see
  // https://stackoverflow.com/questions/49180192/how-to-specify-the-order-in-which-the-style-sheets-appear-in-the-document
  { index: 1 }
);

export { useStyles };
