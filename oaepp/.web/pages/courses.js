/** @jsxImportSource @emotion/react */


import { ErrorBoundary } from "react-error-boundary"
import { Fragment, useCallback, useContext, useEffect, useState } from "react"
import { ColorModeContext, EventLoopContext } from "$/utils/context"
import { Event, getBackendURL, isTrue, refs } from "$/utils/state"
import { jsx, keyframes } from "@emotion/react"
import { WifiOffIcon as LucideWifiOffIcon } from "lucide-react"
import { toast, Toaster } from "sonner"
import env from "$/env.json"
import { Box as RadixThemesBox, Flex as RadixThemesFlex, Grid as RadixThemesGrid, Link as RadixThemesLink, Select as RadixThemesSelect, Table as RadixThemesTable, Text as RadixThemesText } from "@radix-ui/themes"
import NextLink from "next/link"
import NextHead from "next/head"



export function Div_602c14884fa2de27f522fe8f94374b02 () {
  
  const [addEvents, connectErrors] = useContext(EventLoopContext);





  
  return (
    <div css={({ ["position"] : "fixed", ["width"] : "100vw", ["height"] : "0" })} title={("Connection Error: "+((connectErrors.length > 0) ? connectErrors[connectErrors.length - 1].message : ''))}>

<Fragment_f2f0916d2fcc08b7cdf76cec697f0750/>
</div>
  )
}

const pulse = keyframes`
    0% {
        opacity: 0;
    }
    100% {
        opacity: 1;
    }
`


export function Toaster_6e6ebf8d7ce589d59b7d382fb7576edf () {
  
  const { resolvedColorMode } = useContext(ColorModeContext)

  refs['__toast'] = toast
  const [addEvents, connectErrors] = useContext(EventLoopContext);
  const toast_props = ({ ["description"] : ("Check if server is reachable at "+getBackendURL(env.EVENT).href), ["closeButton"] : true, ["duration"] : 120000, ["id"] : "websocket-error" });
  const [userDismissed, setUserDismissed] = useState(false);
  (useEffect(
() => {
    if ((connectErrors.length >= 2)) {
        if (!userDismissed) {
            toast.error(
                `Cannot connect to server: ${((connectErrors.length > 0) ? connectErrors[connectErrors.length - 1].message : '')}.`,
                {...toast_props, onDismiss: () => setUserDismissed(true)},
            )
        }
    } else {
        toast.dismiss("websocket-error");
        setUserDismissed(false);  // after reconnection reset dismissed state
    }
}
, [connectErrors]))




  
  return (
    <Toaster closeButton={false} expand={true} position={"bottom-right"} richColors={true} theme={resolvedColorMode}/>
  )
}

export function Fragment_f2f0916d2fcc08b7cdf76cec697f0750 () {
  
  const [addEvents, connectErrors] = useContext(EventLoopContext);





  
  return (
    <Fragment>

{isTrue((connectErrors.length > 0)) ? (
  <Fragment>

<LucideWifiOffIcon css={({ ["color"] : "crimson", ["zIndex"] : 9999, ["position"] : "fixed", ["bottom"] : "33px", ["right"] : "33px", ["animation"] : (pulse+" 1s infinite") })} size={32}/>
</Fragment>
) : (
  <Fragment/>
)}
</Fragment>
  )
}

export function Errorboundary_33af91293336e0bd1b31f7e4b3fede5a () {
  
  const [addEvents, connectErrors] = useContext(EventLoopContext);


  const on_error_0f5dbf674521530422d73a7946faf6d4 = useCallback(((_error, _info) => (addEvents([(Event("reflex___state____state.reflex___state____frontend_event_exception_state.handle_frontend_exception", ({ ["stack"] : _error["stack"], ["component_stack"] : _info["componentStack"] }), ({  })))], [_error, _info], ({  })))), [addEvents, Event])



  
  return (
    <ErrorBoundary fallbackRender={((event_args) => (jsx("div", ({ ["css"] : ({ ["height"] : "100%", ["width"] : "100%", ["position"] : "absolute", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" }) }), (jsx("div", ({ ["css"] : ({ ["display"] : "flex", ["flexDirection"] : "column", ["gap"] : "1rem" }) }), (jsx("div", ({ ["css"] : ({ ["display"] : "flex", ["flexDirection"] : "column", ["gap"] : "1rem", ["maxWidth"] : "50ch", ["border"] : "1px solid #888888", ["borderRadius"] : "0.25rem", ["padding"] : "1rem" }) }), (jsx("h2", ({ ["css"] : ({ ["fontSize"] : "1.25rem", ["fontWeight"] : "bold" }) }), (jsx(Fragment, ({  }), "An error occurred while rendering this page.")))), (jsx("p", ({ ["css"] : ({ ["opacity"] : "0.75" }) }), (jsx(Fragment, ({  }), "This is an error with the application itself.")))), (jsx("details", ({  }), (jsx("summary", ({ ["css"] : ({ ["padding"] : "0.5rem" }) }), (jsx(Fragment, ({  }), "Error message")))), (jsx("div", ({ ["css"] : ({ ["width"] : "100%", ["maxHeight"] : "50vh", ["overflow"] : "auto", ["background"] : "#000", ["color"] : "#fff", ["borderRadius"] : "0.25rem" }) }), (jsx("div", ({ ["css"] : ({ ["padding"] : "0.5rem", ["width"] : "fit-content" }) }), (jsx("pre", ({  }), (jsx(Fragment, ({  }), event_args.error.stack)))))))), (jsx("button", ({ ["css"] : ({ ["padding"] : "0.35rem 0.75rem", ["margin"] : "0.5rem", ["background"] : "#fff", ["color"] : "#000", ["border"] : "1px solid #000", ["borderRadius"] : "0.25rem", ["fontWeight"] : "bold" }), ["onClick"] : ((...args) => (addEvents([(Event("_call_function", ({ ["function"] : (() => (navigator["clipboard"]["writeText"](event_args.error.stack))), ["callback"] : null }), ({  })))], args, ({  })))) }), (jsx(Fragment, ({  }), "Copy")))))))), (jsx("hr", ({ ["css"] : ({ ["borderColor"] : "currentColor", ["opacity"] : "0.25" }) }))), (jsx("a", ({ ["href"] : "https://reflex.dev" }), (jsx("div", ({ ["css"] : ({ ["display"] : "flex", ["alignItems"] : "baseline", ["justifyContent"] : "center", ["fontFamily"] : "monospace", ["--default-font-family"] : "monospace", ["gap"] : "0.5rem" }) }), (jsx(Fragment, ({  }), "Built with ")), (jsx("svg", ({ ["css"] : ({ ["viewBox"] : "0 0 56 12", ["fill"] : "currentColor" }), ["height"] : "12", ["width"] : "56", ["xmlns"] : "http://www.w3.org/2000/svg" }), (jsx("path", ({ ["d"] : "M0 11.5999V0.399902H8.96V4.8799H6.72V2.6399H2.24V4.8799H6.72V7.1199H2.24V11.5999H0ZM6.72 11.5999V7.1199H8.96V11.5999H6.72Z" }))), (jsx("path", ({ ["d"] : "M11.2 11.5999V0.399902H17.92V2.6399H13.44V4.8799H17.92V7.1199H13.44V9.3599H17.92V11.5999H11.2Z" }))), (jsx("path", ({ ["d"] : "M20.16 11.5999V0.399902H26.88V2.6399H22.4V4.8799H26.88V7.1199H22.4V11.5999H20.16Z" }))), (jsx("path", ({ ["d"] : "M29.12 11.5999V0.399902H31.36V9.3599H35.84V11.5999H29.12Z" }))), (jsx("path", ({ ["d"] : "M38.08 11.5999V0.399902H44.8V2.6399H40.32V4.8799H44.8V7.1199H40.32V9.3599H44.8V11.5999H38.08Z" }))), (jsx("path", ({ ["d"] : "M47.04 4.8799V0.399902H49.28V4.8799H47.04ZM53.76 4.8799V0.399902H56V4.8799H53.76ZM49.28 7.1199V4.8799H53.76V7.1199H49.28ZM47.04 11.5999V7.1199H49.28V11.5999H47.04ZM53.76 11.5999V7.1199H56V11.5999H53.76Z" }))))))))))))))} onError={on_error_0f5dbf674521530422d73a7946faf6d4}>

<Fragment>

<Div_602c14884fa2de27f522fe8f94374b02/>
<Toaster_6e6ebf8d7ce589d59b7d382fb7576edf/>
</Fragment>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["width"] : "100%", ["minHeight"] : "100vh" })} direction={"row"} gap={"0"}>

<RadixThemesBox css={({ ["width"] : "14rem", ["background"] : "white", ["borderRight"] : "1px solid #e5e7eb", ["display"] : "flex", ["flexDirection"] : "column", ["height"] : "100vh", ["position"] : "fixed", ["left"] : "0", ["top"] : "0" })}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["gap"] : "0.625rem", ["paddingInlineStart"] : "1.25rem", ["paddingInlineEnd"] : "1.25rem", ["paddingTop"] : "1.25rem", ["paddingBottom"] : "1.25rem", ["borderBottom"] : "1px solid #f3f4f6" })} direction={"row"} gap={"3"}>

<RadixThemesBox css={({ ["width"] : "2rem", ["height"] : "2rem", ["background"] : "#2563eb", ["borderRadius"] : "0.5rem", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-5 h-5 text-white\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z\"/></svg>" })}/>
</RadixThemesBox>
<RadixThemesText as={"p"} css={({ ["fontWeight"] : "bold", ["color"] : "#1f2937", ["fontSize"] : "0.875rem" })}>

{"OA-EPP"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "1", ["paddingInlineStart"] : "0.75rem", ["paddingInlineEnd"] : "0.75rem", ["paddingTop"] : "1rem", ["paddingBottom"] : "1rem", ["flex"] : "1" })} direction={"column"} gap={"3"}>

<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u4eea\u8868\u76d8"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/courses"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm bg-blue-50 text-blue-700 font-medium"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u8bfe\u7a0b\u5217\u8868"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/assignments"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u4f5c\u4e1a\u63d0\u4ea4"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/grades"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u6210\u7ee9\u4e0e\u53cd\u9988"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/attendance"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u8bfe\u5802\u7b7e\u5230"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/exam"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u5728\u7ebf\u8003\u8bd5"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/profile"} passHref={true}>

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u4e2a\u4eba\u8d44\u6599"}
</RadixThemesText>
</RadixThemesFlex>
</NextLink>
</RadixThemesLink>
</RadixThemesFlex>
<RadixThemesBox css={({ ["paddingInlineStart"] : "1rem", ["paddingInlineEnd"] : "1rem", ["paddingTop"] : "1rem", ["paddingBottom"] : "1rem", ["borderTop"] : "1px solid #f3f4f6" })}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

<RadixThemesBox css={({ ["width"] : "2rem", ["height"] : "2rem", ["borderRadius"] : "9999px", ["background"] : "#dbeafe", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontWeight"] : "bold", ["fontSize"] : "0.875rem", ["color"] : "#1d4ed8" })}>

{"\u5f20"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0" })} direction={"column"} gap={"0"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#1f2937", ["truncate"] : true })}>

{"\u5f20\u4e09"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["truncate"] : true })}>

{"2021001001"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesFlex>
<RadixThemesLink asChild={true} css={({ ["marginTop"] : "0.75rem", ["display"] : "block", ["textAlign"] : "center", ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"none"}>

<NextLink href={"/login"} passHref={true}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["&:hover"] : ({ ["color"] : "#ef4444" }) })}>

{"\u9000\u51fa\u767b\u5f55"}
</RadixThemesText>
</NextLink>
</RadixThemesLink>
</RadixThemesBox>
</RadixThemesBox>
<RadixThemesBox css={({ ["marginLeft"] : "14rem", ["flex"] : "1", ["padding"] : "2rem", ["background"] : "#f9fafb", ["minHeight"] : "100vh" })}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["width"] : "100%" })} direction={"column"} gap={"0"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} direction={"column"} gap={"0"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.25rem", ["fontWeight"] : "bold", ["color"] : "#1f2937" })}>

{"\u8bfe\u7a0b\u5217\u8868"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#9ca3af", ["marginTop"] : "0.125rem" })}>

{"\u5df2\u9009\u8bfe\u7a0b \u00b7 \u5de5\u7a0b\u5b9e\u8df5 1\u20134"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesGrid css={({ ["gridTemplateColumns"] : "repeat(2, 1fr)", ["gap"] : "1.5rem", ["marginBottom"] : "2rem" })}>

<RadixThemesBox css={({ ["position"] : "relative", ["background"] : "white", ["borderRadius"] : "0.75rem", ["border"] : "1px solid #f3f4f6", ["boxShadow"] : "0 1px 3px rgba(0,0,0,0.08)", ["padding"] : "1.5rem" })}>

<Fragment>

{isTrue(false) ? (
  <Fragment>

<RadixThemesBox>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "white", ["background"] : "#2563eb", ["paddingInlineStart"] : "0.75rem", ["paddingInlineEnd"] : "0.75rem", ["paddingTop"] : "0.125rem", ["paddingBottom"] : "0.125rem", ["borderRadius"] : "9999px", ["boxShadow"] : "0 1px 3px rgba(0,0,0,0.2)", ["position"] : "absolute", ["top"] : "-0.625rem", ["right"] : "1rem" })}>

{"\u5f53\u524d\u5b66\u671f"}
</RadixThemesText>
</RadixThemesBox>
</Fragment>
) : (
  <Fragment/>
)}
</Fragment>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["marginBottom"] : "0.75rem" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["flex"] : "1" })} direction={"column"} gap={"3"}>

<RadixThemesBox css={({ ["align"] : "start" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#16a34a", ["background"] : "#dcfce7", ["paddingInlineStart"] : "0.5rem", ["paddingInlineEnd"] : "0.5rem", ["paddingTop"] : "0.125rem", ["paddingBottom"] : "0.125rem", ["borderRadius"] : "9999px" })}>

{"\u5df2\u5b8c\u6210"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "1rem", ["fontWeight"] : "600", ["color"] : "#1f2937", ["marginTop"] : "0.25rem" })}>

{"\u5de5\u7a0b\u5b9e\u8df5 1"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["marginTop"] : "0.125rem" })}>

{"2023 \u79cb \u00b7 \u5171 8 \u7ae0\u8282 \u00b7 8 \u4efb\u52a1"}
</RadixThemesText>
</RadixThemesBox>
</RadixThemesFlex>
<RadixThemesFlex align={"center"} className={"rx-Stack"} direction={"column"} gap={"0"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.5rem", ["fontWeight"] : "bold", ["color"] : "#16a34a" })}>

{"92"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u603b\u8bc4"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesFlex>
<RadixThemesBox css={({ ["marginBottom"] : "0.75rem" })}>

<RadixThemesBox css={({ ["width"] : "100%", ["background"] : "#f3f4f6", ["height"] : "0.375rem", ["borderRadius"] : "9999px" })}>

<RadixThemesBox css={({ ["height"] : "100%", ["background"] : "#16a34a", ["borderRadius"] : "9999px", ["width"] : "100.0%" })}/>
</RadixThemesBox>
</RadixThemesBox>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["flex"] : "1", ["marginBottom"] : "0.5rem" })} direction={"row"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u5b8c\u6210\u8fdb\u5ea6 8/8 \u4efb\u52a1"}
</RadixThemesText>
<Fragment>

{isTrue(false) ? (
  <Fragment>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#ef4444" })}>

{"\u00b7 2 \u9879\u5373\u5c06\u622a\u6b62"}
</RadixThemesText>
</Fragment>
) : (
  <Fragment/>
)}
</Fragment>
</RadixThemesFlex>
<RadixThemesLink asChild={true} css={({ ["fontSize"] : "0.75rem", ["color"] : "#2563eb", ["&:hover"] : ({ ["textDecoration"] : "underline" }) })} underline={"none"}>

<NextLink href={"#"} passHref={true}>

{"\u67e5\u770b\u8bfe\u7a0b\u8be6\u60c5 \u2192"}
</NextLink>
</RadixThemesLink>
</RadixThemesBox>
<RadixThemesBox css={({ ["position"] : "relative", ["background"] : "white", ["borderRadius"] : "0.75rem", ["border"] : "1px solid #f3f4f6", ["boxShadow"] : "0 1px 3px rgba(0,0,0,0.08)", ["padding"] : "1.5rem" })}>

<Fragment>

{isTrue(false) ? (
  <Fragment>

<RadixThemesBox>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "white", ["background"] : "#2563eb", ["paddingInlineStart"] : "0.75rem", ["paddingInlineEnd"] : "0.75rem", ["paddingTop"] : "0.125rem", ["paddingBottom"] : "0.125rem", ["borderRadius"] : "9999px", ["boxShadow"] : "0 1px 3px rgba(0,0,0,0.2)", ["position"] : "absolute", ["top"] : "-0.625rem", ["right"] : "1rem" })}>

{"\u5f53\u524d\u5b66\u671f"}
</RadixThemesText>
</RadixThemesBox>
</Fragment>
) : (
  <Fragment/>
)}
</Fragment>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["marginBottom"] : "0.75rem" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["flex"] : "1" })} direction={"column"} gap={"3"}>

<RadixThemesBox css={({ ["align"] : "start" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#16a34a", ["background"] : "#dcfce7", ["paddingInlineStart"] : "0.5rem", ["paddingInlineEnd"] : "0.5rem", ["paddingTop"] : "0.125rem", ["paddingBottom"] : "0.125rem", ["borderRadius"] : "9999px" })}>

{"\u5df2\u5b8c\u6210"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "1rem", ["fontWeight"] : "600", ["color"] : "#1f2937", ["marginTop"] : "0.25rem" })}>

{"\u5de5\u7a0b\u5b9e\u8df5 2"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["marginTop"] : "0.125rem" })}>

{"2024 \u6625 \u00b7 \u5171 10 \u7ae0\u8282 \u00b7 10 \u4efb\u52a1"}
</RadixThemesText>
</RadixThemesBox>
</RadixThemesFlex>
<RadixThemesFlex align={"center"} className={"rx-Stack"} direction={"column"} gap={"0"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.5rem", ["fontWeight"] : "bold", ["color"] : "#16a34a" })}>

{"88"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u603b\u8bc4"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesFlex>
<RadixThemesBox css={({ ["marginBottom"] : "0.75rem" })}>

<RadixThemesBox css={({ ["width"] : "100%", ["background"] : "#f3f4f6", ["height"] : "0.375rem", ["borderRadius"] : "9999px" })}>

<RadixThemesBox css={({ ["height"] : "100%", ["background"] : "#16a34a", ["borderRadius"] : "9999px", ["width"] : "100.0%" })}/>
</RadixThemesBox>
</RadixThemesBox>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["flex"] : "1", ["marginBottom"] : "0.5rem" })} direction={"row"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u5b8c\u6210\u8fdb\u5ea6 10/10 \u4efb\u52a1"}
</RadixThemesText>
<Fragment>

{isTrue(false) ? (
  <Fragment>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#ef4444" })}>

{"\u00b7 2 \u9879\u5373\u5c06\u622a\u6b62"}
</RadixThemesText>
</Fragment>
) : (
  <Fragment/>
)}
</Fragment>
</RadixThemesFlex>
<RadixThemesLink asChild={true} css={({ ["fontSize"] : "0.75rem", ["color"] : "#2563eb", ["&:hover"] : ({ ["textDecoration"] : "underline" }) })} underline={"none"}>

<NextLink href={"#"} passHref={true}>

{"\u67e5\u770b\u8bfe\u7a0b\u8be6\u60c5 \u2192"}
</NextLink>
</RadixThemesLink>
</RadixThemesBox>
<RadixThemesBox css={({ ["position"] : "relative", ["background"] : "white", ["borderRadius"] : "0.75rem", ["border"] : "1px solid #f3f4f6", ["boxShadow"] : "0 1px 3px rgba(0,0,0,0.08)", ["padding"] : "1.5rem" })}>

<Fragment>

{isTrue(false) ? (
  <Fragment>

<RadixThemesBox>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "white", ["background"] : "#2563eb", ["paddingInlineStart"] : "0.75rem", ["paddingInlineEnd"] : "0.75rem", ["paddingTop"] : "0.125rem", ["paddingBottom"] : "0.125rem", ["borderRadius"] : "9999px", ["boxShadow"] : "0 1px 3px rgba(0,0,0,0.2)", ["position"] : "absolute", ["top"] : "-0.625rem", ["right"] : "1rem" })}>

{"\u5f53\u524d\u5b66\u671f"}
</RadixThemesText>
</RadixThemesBox>
</Fragment>
) : (
  <Fragment/>
)}
</Fragment>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["marginBottom"] : "0.75rem" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["flex"] : "1" })} direction={"column"} gap={"3"}>

<RadixThemesBox css={({ ["align"] : "start" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#16a34a", ["background"] : "#dcfce7", ["paddingInlineStart"] : "0.5rem", ["paddingInlineEnd"] : "0.5rem", ["paddingTop"] : "0.125rem", ["paddingBottom"] : "0.125rem", ["borderRadius"] : "9999px" })}>

{"\u5df2\u5b8c\u6210"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "1rem", ["fontWeight"] : "600", ["color"] : "#1f2937", ["marginTop"] : "0.25rem" })}>

{"\u5de5\u7a0b\u5b9e\u8df5 3"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["marginTop"] : "0.125rem" })}>

{"2024 \u79cb \u00b7 \u5171 12 \u7ae0\u8282 \u00b7 12 \u4efb\u52a1"}
</RadixThemesText>
</RadixThemesBox>
</RadixThemesFlex>
<RadixThemesFlex align={"center"} className={"rx-Stack"} direction={"column"} gap={"0"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.5rem", ["fontWeight"] : "bold", ["color"] : "#16a34a" })}>

{"85"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u603b\u8bc4"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesFlex>
<RadixThemesBox css={({ ["marginBottom"] : "0.75rem" })}>

<RadixThemesBox css={({ ["width"] : "100%", ["background"] : "#f3f4f6", ["height"] : "0.375rem", ["borderRadius"] : "9999px" })}>

<RadixThemesBox css={({ ["height"] : "100%", ["background"] : "#16a34a", ["borderRadius"] : "9999px", ["width"] : "100.0%" })}/>
</RadixThemesBox>
</RadixThemesBox>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["flex"] : "1", ["marginBottom"] : "0.5rem" })} direction={"row"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u5b8c\u6210\u8fdb\u5ea6 12/12 \u4efb\u52a1"}
</RadixThemesText>
<Fragment>

{isTrue(false) ? (
  <Fragment>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#ef4444" })}>

{"\u00b7 2 \u9879\u5373\u5c06\u622a\u6b62"}
</RadixThemesText>
</Fragment>
) : (
  <Fragment/>
)}
</Fragment>
</RadixThemesFlex>
<RadixThemesLink asChild={true} css={({ ["fontSize"] : "0.75rem", ["color"] : "#2563eb", ["&:hover"] : ({ ["textDecoration"] : "underline" }) })} underline={"none"}>

<NextLink href={"#"} passHref={true}>

{"\u67e5\u770b\u8bfe\u7a0b\u8be6\u60c5 \u2192"}
</NextLink>
</RadixThemesLink>
</RadixThemesBox>
<RadixThemesBox css={({ ["position"] : "relative", ["background"] : "white", ["borderRadius"] : "0.75rem", ["border"] : "2px solid border-blue-300", ["boxShadow"] : "0 4px 6px -1px rgba(0,0,0,0.1)", ["padding"] : "1.5rem" })}>

<Fragment>

{isTrue(true) ? (
  <Fragment>

<RadixThemesBox>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "white", ["background"] : "#2563eb", ["paddingInlineStart"] : "0.75rem", ["paddingInlineEnd"] : "0.75rem", ["paddingTop"] : "0.125rem", ["paddingBottom"] : "0.125rem", ["borderRadius"] : "9999px", ["boxShadow"] : "0 1px 3px rgba(0,0,0,0.2)", ["position"] : "absolute", ["top"] : "-0.625rem", ["right"] : "1rem" })}>

{"\u5f53\u524d\u5b66\u671f"}
</RadixThemesText>
</RadixThemesBox>
</Fragment>
) : (
  <Fragment/>
)}
</Fragment>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["marginBottom"] : "0.75rem" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["flex"] : "1" })} direction={"column"} gap={"3"}>

<RadixThemesBox css={({ ["align"] : "start" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#2563eb", ["background"] : "#dbeafe", ["paddingInlineStart"] : "0.5rem", ["paddingInlineEnd"] : "0.5rem", ["paddingTop"] : "0.125rem", ["paddingBottom"] : "0.125rem", ["borderRadius"] : "9999px" })}>

{"\u8fdb\u884c\u4e2d"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "1rem", ["fontWeight"] : "600", ["color"] : "#1f2937", ["marginTop"] : "0.25rem" })}>

{"\u5de5\u7a0b\u5b9e\u8df5 4"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["marginTop"] : "0.125rem" })}>

{"2025 \u6625 \u00b7 \u5171 15 \u7ae0\u8282 \u00b7 15 \u4efb\u52a1"}
</RadixThemesText>
</RadixThemesBox>
</RadixThemesFlex>
<RadixThemesFlex align={"center"} className={"rx-Stack"} direction={"column"} gap={"0"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.5rem", ["fontWeight"] : "bold", ["color"] : "#2563eb" })}>

{"87.5"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u603b\u8bc4"}
</RadixThemesText>
</RadixThemesFlex>
</RadixThemesFlex>
<RadixThemesBox css={({ ["marginBottom"] : "0.75rem" })}>

<RadixThemesBox css={({ ["width"] : "100%", ["background"] : "#f3f4f6", ["height"] : "0.375rem", ["borderRadius"] : "9999px" })}>

<RadixThemesBox css={({ ["height"] : "100%", ["background"] : "#2563eb", ["borderRadius"] : "9999px", ["width"] : "46.666666666666664%" })}/>
</RadixThemesBox>
</RadixThemesBox>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["flex"] : "1", ["marginBottom"] : "0.5rem" })} direction={"row"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u5b8c\u6210\u8fdb\u5ea6 7/15 \u4efb\u52a1"}
</RadixThemesText>
<Fragment>

{isTrue(true) ? (
  <Fragment>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#ef4444" })}>

{"\u00b7 2 \u9879\u5373\u5c06\u622a\u6b62"}
</RadixThemesText>
</Fragment>
) : (
  <Fragment/>
)}
</Fragment>
</RadixThemesFlex>
<RadixThemesLink asChild={true} css={({ ["fontSize"] : "0.75rem", ["color"] : "#2563eb", ["&:hover"] : ({ ["textDecoration"] : "underline" }) })} underline={"none"}>

<NextLink href={"/courses"} passHref={true}>

{"\u67e5\u770b\u8bfe\u7a0b\u8be6\u60c5 \u2192"}
</NextLink>
</RadixThemesLink>
</RadixThemesBox>
</RadixThemesGrid>
<RadixThemesBox css={({ ["background"] : "white", ["borderRadius"] : "0.75rem", ["border"] : "1px solid #f3f4f6", ["boxShadow"] : "0 1px 3px rgba(0,0,0,0.08)", ["padding"] : "1.5rem" })}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["marginBottom"] : "1.25rem" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "600", ["color"] : "#374151" })}>

{"\u5de5\u7a0b\u5b9e\u8df5 4 \u00b7 \u7ae0\u8282\u5217\u8868"}
</RadixThemesText>
<RadixThemesSelect.Root css={({ ["fontSize"] : "0.75rem" })} defaultValue={"\u5168\u90e8\u72b6\u6001"}>

<RadixThemesSelect.Trigger css={({ ["width"] : "auto" })}/>
<RadixThemesSelect.Content>

<RadixThemesSelect.Group>

{""}
<RadixThemesSelect.Item value={"\u5168\u90e8\u72b6\u6001"}>

{"\u5168\u90e8\u72b6\u6001"}
</RadixThemesSelect.Item>
<RadixThemesSelect.Item value={"\u5df2\u5b8c\u6210"}>

{"\u5df2\u5b8c\u6210"}
</RadixThemesSelect.Item>
<RadixThemesSelect.Item value={"\u8fdb\u884c\u4e2d"}>

{"\u8fdb\u884c\u4e2d"}
</RadixThemesSelect.Item>
<RadixThemesSelect.Item value={"\u5f85\u5f00\u59cb"}>

{"\u5f85\u5f00\u59cb"}
</RadixThemesSelect.Item>
</RadixThemesSelect.Group>
</RadixThemesSelect.Content>
</RadixThemesSelect.Root>
</RadixThemesFlex>
<RadixThemesTable.Root css={({ ["width"] : "100%" })}>

<RadixThemesTable.Header>

<RadixThemesTable.Row>

<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#6b7280" })}>

{"\u7ae0\u8282"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#6b7280" })}>

{"\u6807\u9898"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#6b7280" })}>

{"\u622a\u6b62\u65f6\u95f4"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#6b7280" })}>

{"\u72b6\u6001"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#6b7280" })}>

{"\u5f97\u5206"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem" })}>

{""}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
</RadixThemesTable.Row>
</RadixThemesTable.Header>
<RadixThemesTable.Body>

<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"Ch.01"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#1f2937" })}>

{"\u9700\u6c42\u5206\u6790\u65b9\u6cd5"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["fontWeight"] : "normal" })}>

{"2025-03-14"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesBox css={({ ["paddingInlineStart"] : "0.5rem", ["paddingInlineEnd"] : "0.5rem", ["paddingTop"] : "0.125rem", ["paddingBottom"] : "0.125rem", ["borderRadius"] : "9999px", ["background"] : "#dcfce7", ["color"] : "#16a34a", ["display"] : "inline-block" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem" })}>

{"\u5df2\u6279\u6539"}
</RadixThemesText>
</RadixThemesBox>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "600", ["color"] : "#16a34a" })}>

{"9.5/10"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesLink asChild={true} css={({ ["fontSize"] : "0.75rem", ["color"] : "#2563eb", ["&:hover"] : ({ ["textDecoration"] : "underline" }), ["textAlign"] : "right" })} underline={"none"}>

<NextLink href={"/grades"} passHref={true}>

{"\u67e5\u770b"}
</NextLink>
</RadixThemesLink>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"Ch.02"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#1f2937" })}>

{"\u7528\u4f8b\u5efa\u6a21"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["fontWeight"] : "normal" })}>

{"2025-03-21"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesBox css={({ ["paddingInlineStart"] : "0.5rem", ["paddingInlineEnd"] : "0.5rem", ["paddingTop"] : "0.125rem", ["paddingBottom"] : "0.125rem", ["borderRadius"] : "9999px", ["background"] : "#dcfce7", ["color"] : "#16a34a", ["display"] : "inline-block" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem" })}>

{"\u5df2\u6279\u6539"}
</RadixThemesText>
</RadixThemesBox>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "600", ["color"] : "#16a34a" })}>

{"8/10"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesLink asChild={true} css={({ ["fontSize"] : "0.75rem", ["color"] : "#2563eb", ["&:hover"] : ({ ["textDecoration"] : "underline" }), ["textAlign"] : "right" })} underline={"none"}>

<NextLink href={"/grades"} passHref={true}>

{"\u67e5\u770b"}
</NextLink>
</RadixThemesLink>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"Ch.06"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#1f2937" })}>

{"\u6570\u636e\u5e93\u8bbe\u8ba1"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["fontWeight"] : "normal" })}>

{"2025-05-09"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesBox css={({ ["paddingInlineStart"] : "0.5rem", ["paddingInlineEnd"] : "0.5rem", ["paddingTop"] : "0.125rem", ["paddingBottom"] : "0.125rem", ["borderRadius"] : "9999px", ["background"] : "#fef9c3", ["color"] : "#ca8a04", ["display"] : "inline-block" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem" })}>

{"\u5f85\u6279\u6539"}
</RadixThemesText>
</RadixThemesBox>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["color"] : "#9ca3af" })}>

{"\u2014"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesLink asChild={true} css={({ ["fontSize"] : "0.75rem", ["color"] : "#2563eb", ["&:hover"] : ({ ["textDecoration"] : "underline" }), ["textAlign"] : "right" })} underline={"none"}>

<NextLink href={"/grades"} passHref={true}>

{"\u67e5\u770b"}
</NextLink>
</RadixThemesLink>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"Ch.07"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#1f2937" })}>

{"\u8f6f\u4ef6\u9700\u6c42\u89c4\u683c\u8bf4\u660e\u4e66"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#dc2626", ["fontWeight"] : "500" })}>

{"2025-05-27 \u26a0\ufe0f"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesBox css={({ ["paddingInlineStart"] : "0.5rem", ["paddingInlineEnd"] : "0.5rem", ["paddingTop"] : "0.125rem", ["paddingBottom"] : "0.125rem", ["borderRadius"] : "9999px", ["background"] : "#fef2f2", ["color"] : "#dc2626", ["display"] : "inline-block" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem" })}>

{"\u5f85\u63d0\u4ea4"}
</RadixThemesText>
</RadixThemesBox>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["color"] : "#9ca3af" })}>

{"\u2014"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesLink asChild={true} css={({ ["fontSize"] : "0.75rem", ["color"] : "#2563eb", ["&:hover"] : ({ ["textDecoration"] : "underline" }), ["textAlign"] : "right" })} underline={"none"}>

<NextLink href={"/assignments"} passHref={true}>

{"\u63d0\u4ea4"}
</NextLink>
</RadixThemesLink>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"Ch.08"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#1f2937" })}>

{"\u7cfb\u7edf\u8bbe\u8ba1\u6587\u6863"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["fontWeight"] : "normal" })}>

{"2025-06-03"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesBox css={({ ["paddingInlineStart"] : "0.5rem", ["paddingInlineEnd"] : "0.5rem", ["paddingTop"] : "0.125rem", ["paddingBottom"] : "0.125rem", ["borderRadius"] : "9999px", ["background"] : "#f3f4f6", ["color"] : "#6b7280", ["display"] : "inline-block" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem" })}>

{"\u672a\u5f00\u59cb"}
</RadixThemesText>
</RadixThemesBox>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["color"] : "#9ca3af" })}>

{"\u2014"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesLink asChild={true} css={({ ["fontSize"] : "0.75rem", ["color"] : "#2563eb", ["&:hover"] : ({ ["textDecoration"] : "underline" }), ["textAlign"] : "right" })} underline={"none"}>

<NextLink href={"/courses"} passHref={true}>

{"\u67e5\u770b"}
</NextLink>
</RadixThemesLink>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
</RadixThemesTable.Body>
</RadixThemesTable.Root>
</RadixThemesBox>
</RadixThemesFlex>
</RadixThemesBox>
</RadixThemesFlex>
<NextHead>

<title>

{"OA-EPP \u00b7 \u8bfe\u7a0b\u5217\u8868"}
</title>
<meta content={"favicon.ico"} property={"og:image"}/>
</NextHead>
</ErrorBoundary>
  )
}

export default function Component() {
    




  return (
    <Errorboundary_33af91293336e0bd1b31f7e4b3fede5a/>
  )
}
