/** @jsxImportSource @emotion/react */


import { ErrorBoundary } from "react-error-boundary"
import { Fragment, useCallback, useContext, useEffect, useState } from "react"
import { ColorModeContext, EventLoopContext, StateContexts } from "$/utils/context"
import { Event, getBackendURL, isTrue, refs } from "$/utils/state"
import { jsx, keyframes } from "@emotion/react"
import { WifiOffIcon as LucideWifiOffIcon } from "lucide-react"
import { toast, Toaster } from "sonner"
import env from "$/env.json"
import { Box as RadixThemesBox, Button as RadixThemesButton, Flex as RadixThemesFlex, Link as RadixThemesLink, Text as RadixThemesText, TextField as RadixThemesTextField } from "@radix-ui/themes"
import { DebounceInput } from "react-debounce-input"
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

export function Debounceinput_df967cd4979b4869ff7bc9469e7b34ca () {
  
  const reflex___state____state__oaepp___pages___login____login_state = useContext(StateContexts.reflex___state____state__oaepp___pages___login____login_state)
  const [addEvents, connectErrors] = useContext(EventLoopContext);


  const on_change_124ce6b3997efac9660de7a8f4983ce1 = useCallback(((_e) => (addEvents([(Event("reflex___state____state.oaepp___pages___login____login_state.set_student_id", ({ ["value"] : _e["target"]["value"] }), ({  })))], [_e], ({  })))), [addEvents, Event])



  
  return (
    <DebounceInput css={({ ["width"] : "100%", ["padding"] : "0.625rem 1rem", ["border"] : "1px solid #d1d5db", ["borderRadius"] : "0.5rem", ["fontSize"] : "0.875rem" })} debounceTimeout={300} element={RadixThemesTextField.Root} onChange={on_change_124ce6b3997efac9660de7a8f4983ce1} placeholder={"\u8bf7\u8f93\u5165\u5b66\u53f7"} value={reflex___state____state__oaepp___pages___login____login_state.student_id}/>
  )
}

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

const pulse = keyframes`
    0% {
        opacity: 0;
    }
    100% {
        opacity: 1;
    }
`


export function Button_0d57b107323dff8e1311856b27da1b54 () {
  
  const [addEvents, connectErrors] = useContext(EventLoopContext);


  const on_click_62f1bb2e27f6f633e35387e31e06d5e3 = useCallback(((...args) => (addEvents([(Event("reflex___state____state.oaepp___pages___login____login_state.login", ({  }), ({  })))], args, ({  })))), [addEvents, Event])



  
  return (
    <RadixThemesButton css={({ ["background"] : "#2563eb", ["&:hover"] : ({ ["background"] : "#1d4ed8" }), ["color"] : "white", ["fontWeight"] : "600", ["padding"] : "0.625rem 0", ["width"] : "100%", ["borderRadius"] : "0.5rem", ["fontSize"] : "0.875rem", ["marginTop"] : "0.5rem" })} onClick={on_click_62f1bb2e27f6f633e35387e31e06d5e3}>

{"\u767b \u5f55"}
</RadixThemesButton>
  )
}

export function Errorboundary_578ef6dbe9f41f2532948eba98417682 () {
  
  const [addEvents, connectErrors] = useContext(EventLoopContext);


  const on_error_0f5dbf674521530422d73a7946faf6d4 = useCallback(((_error, _info) => (addEvents([(Event("reflex___state____state.reflex___state____frontend_event_exception_state.handle_frontend_exception", ({ ["stack"] : _error["stack"], ["component_stack"] : _info["componentStack"] }), ({  })))], [_error, _info], ({  })))), [addEvents, Event])



  
  return (
    <ErrorBoundary fallbackRender={((event_args) => (jsx("div", ({ ["css"] : ({ ["height"] : "100%", ["width"] : "100%", ["position"] : "absolute", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" }) }), (jsx("div", ({ ["css"] : ({ ["display"] : "flex", ["flexDirection"] : "column", ["gap"] : "1rem" }) }), (jsx("div", ({ ["css"] : ({ ["display"] : "flex", ["flexDirection"] : "column", ["gap"] : "1rem", ["maxWidth"] : "50ch", ["border"] : "1px solid #888888", ["borderRadius"] : "0.25rem", ["padding"] : "1rem" }) }), (jsx("h2", ({ ["css"] : ({ ["fontSize"] : "1.25rem", ["fontWeight"] : "bold" }) }), (jsx(Fragment, ({  }), "An error occurred while rendering this page.")))), (jsx("p", ({ ["css"] : ({ ["opacity"] : "0.75" }) }), (jsx(Fragment, ({  }), "This is an error with the application itself.")))), (jsx("details", ({  }), (jsx("summary", ({ ["css"] : ({ ["padding"] : "0.5rem" }) }), (jsx(Fragment, ({  }), "Error message")))), (jsx("div", ({ ["css"] : ({ ["width"] : "100%", ["maxHeight"] : "50vh", ["overflow"] : "auto", ["background"] : "#000", ["color"] : "#fff", ["borderRadius"] : "0.25rem" }) }), (jsx("div", ({ ["css"] : ({ ["padding"] : "0.5rem", ["width"] : "fit-content" }) }), (jsx("pre", ({  }), (jsx(Fragment, ({  }), event_args.error.stack)))))))), (jsx("button", ({ ["css"] : ({ ["padding"] : "0.35rem 0.75rem", ["margin"] : "0.5rem", ["background"] : "#fff", ["color"] : "#000", ["border"] : "1px solid #000", ["borderRadius"] : "0.25rem", ["fontWeight"] : "bold" }), ["onClick"] : ((...args) => (addEvents([(Event("_call_function", ({ ["function"] : (() => (navigator["clipboard"]["writeText"](event_args.error.stack))), ["callback"] : null }), ({  })))], args, ({  })))) }), (jsx(Fragment, ({  }), "Copy")))))))), (jsx("hr", ({ ["css"] : ({ ["borderColor"] : "currentColor", ["opacity"] : "0.25" }) }))), (jsx("a", ({ ["href"] : "https://reflex.dev" }), (jsx("div", ({ ["css"] : ({ ["display"] : "flex", ["alignItems"] : "baseline", ["justifyContent"] : "center", ["fontFamily"] : "monospace", ["--default-font-family"] : "monospace", ["gap"] : "0.5rem" }) }), (jsx(Fragment, ({  }), "Built with ")), (jsx("svg", ({ ["css"] : ({ ["viewBox"] : "0 0 56 12", ["fill"] : "currentColor" }), ["height"] : "12", ["width"] : "56", ["xmlns"] : "http://www.w3.org/2000/svg" }), (jsx("path", ({ ["d"] : "M0 11.5999V0.399902H8.96V4.8799H6.72V2.6399H2.24V4.8799H6.72V7.1199H2.24V11.5999H0ZM6.72 11.5999V7.1199H8.96V11.5999H6.72Z" }))), (jsx("path", ({ ["d"] : "M11.2 11.5999V0.399902H17.92V2.6399H13.44V4.8799H17.92V7.1199H13.44V9.3599H17.92V11.5999H11.2Z" }))), (jsx("path", ({ ["d"] : "M20.16 11.5999V0.399902H26.88V2.6399H22.4V4.8799H26.88V7.1199H22.4V11.5999H20.16Z" }))), (jsx("path", ({ ["d"] : "M29.12 11.5999V0.399902H31.36V9.3599H35.84V11.5999H29.12Z" }))), (jsx("path", ({ ["d"] : "M38.08 11.5999V0.399902H44.8V2.6399H40.32V4.8799H44.8V7.1199H40.32V9.3599H44.8V11.5999H38.08Z" }))), (jsx("path", ({ ["d"] : "M47.04 4.8799V0.399902H49.28V4.8799H47.04ZM53.76 4.8799V0.399902H56V4.8799H53.76ZM49.28 7.1199V4.8799H53.76V7.1199H49.28ZM47.04 11.5999V7.1199H49.28V11.5999H47.04ZM53.76 11.5999V7.1199H56V11.5999H53.76Z" }))))))))))))))} onError={on_error_0f5dbf674521530422d73a7946faf6d4}>

<Fragment>

<Div_602c14884fa2de27f522fe8f94374b02/>
<Toaster_6e6ebf8d7ce589d59b7d382fb7576edf/>
</Fragment>
<RadixThemesBox css={({ ["width"] : "100%", ["minHeight"] : "100vh", ["background"] : "linear-gradient(135deg, #eff6ff, #dbeafe)" })}>

<RadixThemesFlex css={({ ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center", ["width"] : "100%", ["minHeight"] : "100vh" })}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["background"] : "white", ["borderRadius"] : "1rem", ["boxShadow"] : "0 10px 25px rgba(0,0,0,0.1)", ["padding"] : "2rem", ["width"] : "100%", ["maxWidth"] : "28rem" })} direction={"column"} gap={"3"}>

<RadixThemesBox css={({ ["width"] : "4rem", ["height"] : "4rem", ["background"] : "#2563eb", ["borderRadius"] : "1rem", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-9 h-9 text-white\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z</path></svg>" })}/>
</RadixThemesBox>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.5rem", ["fontWeight"] : "bold", ["color"] : "#1f2937" })}>

{"\u5de5\u7a0b\u5b9e\u8df5\u7ba1\u7406\u5e73\u53f0"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280", ["marginBottom"] : "1.5rem" })}>

{"OA-EPP \u00b7 Engineering Practice Platform"}
</RadixThemesText>
<Fragment_c490c74026f52f712d29b3f2516ab60c/>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0.5rem", ["width"] : "100%" })} direction={"column"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#4b5563" })}>

{"\u5b66\u53f7"}
</RadixThemesText>
<Debounceinput_df967cd4979b4869ff7bc9469e7b34ca/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#4b5563" })}>

{"\u5bc6\u7801"}
</RadixThemesText>
<Debounceinput_62811b4e81fbdd37b1462e6293c21eeb/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["marginTop"] : "0.25rem" })}>

{"\u521d\u59cb\u5bc6\u7801\u4e3a\u5b66\u53f7\uff0c\u8bf7\u767b\u5f55\u540e\u53ca\u65f6\u4fee\u6539"}
</RadixThemesText>
<Button_0d57b107323dff8e1311856b27da1b54/>
<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["width"] : "100%", ["marginTop"] : "1.25rem", ["marginBottom"] : "1.25rem" })} direction={"row"} gap={"3"}>

<RadixThemesBox css={({ ["borderTop"] : "1px solid #e5e7eb", ["flex"] : "1" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["marginInlineStart"] : "0.75rem", ["marginInlineEnd"] : "0.75rem" })}>

{"\u6216"}
</RadixThemesText>
<RadixThemesBox css={({ ["borderTop"] : "1px solid #e5e7eb", ["flex"] : "1" })}/>
</RadixThemesFlex>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["textAlign"] : "center" })}>

{"\u5fd8\u8bb0\u5bc6\u7801\uff1f\u8bf7\u8054\u7cfb\u6559\u5e08\u6216\u52a9\u6559\u91cd\u7f6e\u3002"}
</RadixThemesText>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "1.5rem", ["marginTop"] : "1.25rem" })} direction={"row"} justify={"center"} gap={"3"}>

<RadixThemesLink asChild={true} css={({ ["fontSize"] : "0.75rem", ["color"] : "#2563eb", ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"hover"}>

<NextLink href={"/"} passHref={true}>

{"\u5b66\u751f\u7aef"}
</NextLink>
</RadixThemesLink>
<RadixThemesLink asChild={true} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280", ["&:hover"] : ({ ["color"] : "var(--accent-8)" }) })} underline={"hover"}>

<NextLink href={"/admin_students"} passHref={true}>

{"\u6559\u5e08\u7aef"}
</NextLink>
</RadixThemesLink>
</RadixThemesFlex>
</RadixThemesFlex>
</RadixThemesFlex>
</RadixThemesFlex>
</RadixThemesBox>
<NextHead>

<title>

{"OA-EPP \u00b7 \u767b\u5f55"}
</title>
<meta content={"favicon.ico"} property={"og:image"}/>
</NextHead>
</ErrorBoundary>
  )
}

export function Debounceinput_62811b4e81fbdd37b1462e6293c21eeb () {
  
  const reflex___state____state__oaepp___pages___login____login_state = useContext(StateContexts.reflex___state____state__oaepp___pages___login____login_state)
  const [addEvents, connectErrors] = useContext(EventLoopContext);


  const on_change_388634cc0273e7def9c9c1b8f46a346b = useCallback(((_e) => (addEvents([(Event("reflex___state____state.oaepp___pages___login____login_state.set_password", ({ ["value"] : _e["target"]["value"] }), ({  })))], [_e], ({  })))), [addEvents, Event])



  
  return (
    <DebounceInput css={({ ["width"] : "100%", ["padding"] : "0.625rem 1rem", ["border"] : "1px solid #d1d5db", ["borderRadius"] : "0.5rem", ["fontSize"] : "0.875rem" })} debounceTimeout={300} element={RadixThemesTextField.Root} onChange={on_change_388634cc0273e7def9c9c1b8f46a346b} placeholder={"\u8bf7\u8f93\u5165\u5bc6\u7801"} type={"password"} value={reflex___state____state__oaepp___pages___login____login_state.password}/>
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

export function Fragment_c490c74026f52f712d29b3f2516ab60c () {
  
  const reflex___state____state__oaepp___pages___login____login_state = useContext(StateContexts.reflex___state____state__oaepp___pages___login____login_state)





  
  return (
    <Fragment>

{isTrue(!((reflex___state____state__oaepp___pages___login____login_state.error_msg === ""))) ? (
  <Fragment>

<RadixThemesBox css={({ ["background"] : "#fef2f2", ["border"] : "1px solid #fecaca", ["color"] : "#b91c1c", ["fontSize"] : "0.875rem", ["padding"] : "0.75rem 1rem", ["borderRadius"] : "0.5rem", ["width"] : "100%" })}>

<RadixThemesText as={"p"}>

{reflex___state____state__oaepp___pages___login____login_state.error_msg}
</RadixThemesText>
</RadixThemesBox>
</Fragment>
) : (
  <Fragment/>
)}
</Fragment>
  )
}

export default function Component() {
    




  return (
    <Errorboundary_578ef6dbe9f41f2532948eba98417682/>
  )
}
