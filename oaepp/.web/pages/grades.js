/** @jsxImportSource @emotion/react */


import { ErrorBoundary } from "react-error-boundary"
import { Fragment, useCallback, useContext, useEffect, useState } from "react"
import { ColorModeContext, EventLoopContext } from "$/utils/context"
import { Event, getBackendURL, isTrue, refs } from "$/utils/state"
import { jsx, keyframes } from "@emotion/react"
import { WifiOffIcon as LucideWifiOffIcon } from "lucide-react"
import { toast, Toaster } from "sonner"
import env from "$/env.json"
import { Box as RadixThemesBox, Flex as RadixThemesFlex, Grid as RadixThemesGrid, Link as RadixThemesLink, Table as RadixThemesTable, Text as RadixThemesText } from "@radix-ui/themes"
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


export function Errorboundary_59401012a381ea4ac4dd9131cc4a29b6 () {
  
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

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

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

<RadixThemesFlex align={"center"} className={"rx-Stack flex items-center gap-3 px-3 py-2 rounded-lg text-sm bg-blue-50 text-blue-700 font-medium"} css={({ ["gap"] : "0.75rem" })} direction={"row"} gap={"3"}>

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

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["marginBottom"] : "1.5rem", ["width"] : "100%" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0" })} direction={"column"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.25rem", ["fontWeight"] : "bold", ["color"] : "#1f2937" })}>

{"\u6210\u7ee9\u4e0e\u53cd\u9988"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#9ca3af", ["marginTop"] : "0.125rem" })}>

{"\u5de5\u7a0b\u5b9e\u8df5 4 \u00b7 \u7efc\u5408\u603b\u5206 87.5 / 100"}
</RadixThemesText>
</RadixThemesFlex>
<button className={"bg-green-600 hover:bg-green-700 text-white text-sm px-4 py-2 rounded-lg transition"}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["gap"] : "0.5rem" })} direction={"row"} gap={"3"}>

<div className={"rx-Html"} dangerouslySetInnerHTML={({ ["__html"] : "<svg class=\"w-4 h-4\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\"><path stroke-linecap=\"round\" stroke-linejoin=\"round\" stroke-width=\"2\" d=\"M12 10v6m0 0l-3-3m3 3l3-2m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z\"/></svg>" })}/>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem" })}>

{"\u4e0b\u8f7d\u6210\u7ee9\u5355 Excel"}
</RadixThemesText>
</RadixThemesFlex>
</button>
</RadixThemesFlex>
<RadixThemesGrid css={({ ["gridTemplateColumns"] : "repeat(4, 1fr)", ["gap"] : "1.25rem", ["marginBottom"] : "2rem", ["width"] : "100%" })}>

<RadixThemesBox className={"bg-white rounded-xl border border-gray-100 shadow-sm p-5"}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["marginBottom"] : "0.5rem" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["fontWeight"] : "500" })}>

{"\u51fa\u52e4\u5f97\u5206"}
</RadixThemesText>
<RadixThemesText as={"p"} className={"text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full"}>

{"\u5df2\u66f4\u65b0"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesFlex align={"end"} className={"rx-Stack"} css={({ ["gap"] : "0.25rem" })} direction={"row"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.5rem", ["fontWeight"] : "bold", ["color"] : "#16a34a" })}>

{"18"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#9ca3af" })}>

{"/ 20"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesBox css={({ ["width"] : "100%", ["background"] : "#f3f4f6", ["height"] : "0.375rem", ["borderRadius"] : "9999px", ["marginTop"] : "0.5rem" })}>

<RadixThemesBox css={({ ["width"] : "90.0%", ["height"] : "100%", ["background"] : "#16a34a", ["borderRadius"] : "9999px" })}/>
</RadixThemesBox>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["marginTop"] : "0.375rem" })}>

{"\u51fa\u52e4 18/20 \u6b21 \u00b7 \u7f3a\u52e4 2 \u6b21"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={"bg-white rounded-xl border border-gray-100 shadow-sm p-5"}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["marginBottom"] : "0.5rem" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["fontWeight"] : "500" })}>

{"\u8003\u8bd5\u5f97\u5206"}
</RadixThemesText>
<RadixThemesText as={"p"} className={"text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full"}>

{"\u5df2\u66f4\u65b0"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesFlex align={"end"} className={"rx-Stack"} css={({ ["gap"] : "0.25rem" })} direction={"row"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.5rem", ["fontWeight"] : "bold", ["color"] : "#9333ea" })}>

{"24"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#9ca3af" })}>

{"/ 30"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesBox css={({ ["width"] : "100%", ["background"] : "#f3f4f6", ["height"] : "0.375rem", ["borderRadius"] : "9999px", ["marginTop"] : "0.5rem" })}>

<RadixThemesBox css={({ ["width"] : "80.0%", ["height"] : "100%", ["background"] : "#9333ea", ["borderRadius"] : "9999px" })}/>
</RadixThemesBox>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["marginTop"] : "0.375rem" })}>

{"3 \u6b21\u8003\u8bd5\u5747\u5df2\u51fa\u5206"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={"bg-white rounded-xl border border-gray-100 shadow-sm p-5"}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["marginBottom"] : "0.5rem" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["fontWeight"] : "500" })}>

{"\u4ee3\u7801\u63d0\u4ea4"}
</RadixThemesText>
<RadixThemesText as={"p"} className={"text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full"}>

{"\u90e8\u5206\u5f85\u6279"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesFlex align={"end"} className={"rx-Stack"} css={({ ["gap"] : "0.25rem" })} direction={"row"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.5rem", ["fontWeight"] : "bold", ["color"] : "#ea580c" })}>

{"32"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#9ca3af" })}>

{"/ 40"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesBox css={({ ["width"] : "100%", ["background"] : "#f3f4f6", ["height"] : "0.375rem", ["borderRadius"] : "9999px", ["marginTop"] : "0.5rem" })}>

<RadixThemesBox css={({ ["width"] : "80.0%", ["height"] : "100%", ["background"] : "#ea580c", ["borderRadius"] : "9999px" })}/>
</RadixThemesBox>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["marginTop"] : "0.375rem" })}>

{"5 \u5df2\u6279 \u00b7 2 \u5f85\u6279"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesBox className={"bg-white rounded-xl border border-gray-100 shadow-sm p-5"}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["marginBottom"] : "0.5rem" })} direction={"row"} justify={"between"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["fontWeight"] : "500" })}>

{"PR \u8d21\u732e"}
</RadixThemesText>
<RadixThemesText as={"p"} className={"text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full"}>

{"\u5df2\u66f4\u65b0"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesFlex align={"end"} className={"rx-Stack"} css={({ ["gap"] : "0.25rem" })} direction={"row"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.5rem", ["fontWeight"] : "bold", ["color"] : "#2563eb" })}>

{"13.5"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#9ca3af" })}>

{"/ 10"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesBox css={({ ["width"] : "100%", ["background"] : "#f3f4f6", ["height"] : "0.375rem", ["borderRadius"] : "9999px", ["marginTop"] : "0.5rem" })}>

<RadixThemesBox css={({ ["width"] : "100%", ["height"] : "100%", ["background"] : "#2563eb", ["borderRadius"] : "9999px" })}/>
</RadixThemesBox>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af", ["marginTop"] : "0.375rem" })}>

{"\u8d85\u989d\u52a0\u5206 \u00b7 9 \u6b21 PR \u5ba1\u67e5"}
</RadixThemesText>
</RadixThemesBox>
</RadixThemesGrid>
<RadixThemesBox className={"bg-white rounded-xl border border-gray-100 shadow-sm"} css={({ ["width"] : "100%" })}>

<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["borderBottom"] : "1px solid #f3f4f6" })} direction={"row"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#2563eb", ["borderBottom"] : "2px solid #2563eb", ["paddingTop"] : "0.75rem", ["paddingBottom"] : "0.75rem", ["paddingInlineStart"] : "1rem", ["paddingInlineEnd"] : "1rem" })}>

{"\u4ee3\u7801\u8bc4\u9605\u8be6\u60c5"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280", ["&:hover"] : ({ ["color"] : "#374151" }), ["paddingTop"] : "0.75rem", ["paddingBottom"] : "0.75rem", ["paddingInlineStart"] : "1rem", ["paddingInlineEnd"] : "1rem" })}>

{"\u8003\u8bd5\u6210\u7ee9"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280", ["&:hover"] : ({ ["color"] : "#374151" }), ["paddingTop"] : "0.75rem", ["paddingBottom"] : "0.75rem", ["paddingInlineStart"] : "1rem", ["paddingInlineEnd"] : "1rem" })}>

{"\u51fa\u52e4\u8bb0\u5f55"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#6b7280", ["&:hover"] : ({ ["color"] : "#374151" }), ["paddingTop"] : "0.75rem", ["paddingBottom"] : "0.75rem", ["paddingInlineStart"] : "1rem", ["paddingInlineEnd"] : "1rem" })}>

{"\u65f6\u95f4\u7ebf"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesBox css={({ ["padding"] : "1.25rem" })}>

<RadixThemesTable.Root css={({ ["width"] : "100%" })}>

<RadixThemesTable.Header>

<RadixThemesTable.Row>

<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#9ca3af" })}>

{"\u4efb\u52a1"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#9ca3af" })}>

{"\u5f97\u5206"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#9ca3af" })}>

{"\u6279\u6539\u4eba"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#9ca3af" })}>

{"\u6279\u6539\u65f6\u95f4"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["fontWeight"] : "500", ["color"] : "#9ca3af" })}>

{"\u72b6\u6001"}
</RadixThemesText>
</RadixThemesTable.ColumnHeaderCell>
<RadixThemesTable.ColumnHeaderCell>

{""}
</RadixThemesTable.ColumnHeaderCell>
</RadixThemesTable.Row>
</RadixThemesTable.Header>
<RadixThemesTable.Body>

<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#1f2937" })}>

{"\u7b2c5\u7ae0 \u7cfb\u7edf\u67b6\u6784\u8bbe\u8ba1"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontWeight"] : "bold", ["color"] : "#16a34a" })}>

{"9 / 10"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280" })}>

{"\u674e\u56db\uff08\u6559\u5e08\uff09"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"2025-05-02"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full"}>

{"\u5df2\u6279\u6539"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell css={({ ["textAlign"] : "right" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#3b82f6", ["&:hover"] : ({ ["textDecoration"] : "underline" }) })}>

{"\u67e5\u770b\u8bc4\u8bed"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#1f2937" })}>

{"\u7b2c4\u7ae0 \u7528\u4f8b\u5206\u6790"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontWeight"] : "bold", ["color"] : "#ea580c" })}>

{"7 / 10"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280" })}>

{"\u674e\u56db\uff08\u6559\u5e08\uff09"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"2025-04-25"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full"}>

{"\u8fdf\u4ea4\u6263\u5206"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell css={({ ["textAlign"] : "right" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#3b82f6", ["&:hover"] : ({ ["textDecoration"] : "underline" }) })}>

{"\u67e5\u770b\u8bc4\u8bed"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
<RadixThemesTable.Row css={({ ["borderBottom"] : "1px solid #f9fafb" })}>

<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "500", ["color"] : "#1f2937" })}>

{"\u7b2c6\u7ae0 \u6570\u636e\u5e93\u8bbe\u8ba1"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontWeight"] : "bold", ["color"] : "#9ca3af" })}>

{"\u2014"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280" })}>

{"\u2014"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"\u2014"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell>

<RadixThemesText as={"p"} className={"text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full"}>

{"\u5f85\u6279\u6539"}
</RadixThemesText>
</RadixThemesTable.Cell>
<RadixThemesTable.Cell css={({ ["textAlign"] : "right" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#3b82f6", ["&:hover"] : ({ ["textDecoration"] : "underline" }) })}>

{"\u67e5\u770b\u8bc4\u8bed"}
</RadixThemesText>
</RadixThemesTable.Cell>
</RadixThemesTable.Row>
</RadixThemesTable.Body>
</RadixThemesTable.Root>
<RadixThemesBox css={({ ["border"] : "1px solid #bfdbfe", ["background"] : "#eff6ff", ["borderRadius"] : "0.75rem", ["padding"] : "1.25rem", ["marginTop"] : "1.5rem" })}>

<RadixThemesFlex align={"center"} className={"rx-Stack"} css={({ ["gap"] : "0.75rem", ["marginBottom"] : "0.75rem" })} direction={"row"} gap={"3"}>

<RadixThemesBox css={({ ["width"] : "2rem", ["height"] : "2rem", ["borderRadius"] : "9999px", ["background"] : "#bfdbfe", ["display"] : "flex", ["alignItems"] : "center", ["justifyContent"] : "center" })}>

<RadixThemesText as={"p"} css={({ ["fontWeight"] : "bold", ["fontSize"] : "0.875rem", ["color"] : "#1d4ed8" })}>

{"\u674e"}
</RadixThemesText>
</RadixThemesBox>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0" })} direction={"column"} gap={"3"}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["fontWeight"] : "600", ["color"] : "#1f2937" })}>

{"\u7b2c5\u7ae0\u8bc4\u8bed \u00b7 \u674e\u56db\uff08\u6559\u5e08\uff09"}
</RadixThemesText>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#9ca3af" })}>

{"2025-05-02 \u6279\u6539"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "1.125rem", ["fontWeight"] : "bold", ["color"] : "#16a34a", ["marginLeft"] : "auto" })}>

{"9/10"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.875rem", ["color"] : "#374151", ["lineHeight"] : "1.625", ["marginBottom"] : "0.75rem" })}>

{"\u6574\u4f53\u67b6\u6784\u6e05\u6670\uff0c\u5206\u5c42\u5408\u7406\uff0c\u5bf9 Reflex \u5168\u6808\u6a21\u5f0f\u7406\u89e3\u5230\u4f4d\u3002\u5efa\u8bae\u8865\u5145\u670d\u52a1\u5c42\uff08Service Layer\uff09\u804c\u8d23\u5212\u5206\u8bf4\u660e\uff0c\u907f\u514d State \u7c7b\u8fc7\u91cd\u3002\u7ec4\u4ef6\u547d\u540d\u89c4\u8303\u6027\u6709\u5f85\u63d0\u5347\uff0c\u53c2\u8003\u56e2\u961f\u547d\u540d\u89c4\u8303\u7edf\u4e00\u98ce\u683c\u3002"}
</RadixThemesText>
<RadixThemesFlex align={"start"} className={"rx-Stack"} css={({ ["gap"] : "0.5rem", ["flexWrap"] : "wrap", ["marginBottom"] : "0.75rem" })} direction={"row"} gap={"3"}>

<RadixThemesText as={"p"} className={"text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded"}>

{"\u6263\u5206\uff1a-1 \u00b7 \u547d\u540d\u89c4\u8303"}
</RadixThemesText>
<RadixThemesText as={"p"} className={"text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded"}>

{"\u5efa\u8bae\uff1a\u8865\u5145\u670d\u52a1\u5c42\u8bf4\u660e"}
</RadixThemesText>
</RadixThemesFlex>
<RadixThemesBox css={({ ["borderTop"] : "1px solid #bfdbfe", ["paddingTop"] : "0.75rem" })}>

<RadixThemesText as={"p"} css={({ ["fontSize"] : "0.75rem", ["color"] : "#6b7280", ["marginBottom"] : "0.5rem" })}>

{"\u6b64\u4efb\u52a1\u5141\u8bb8\u4e8c\u6b21\u63d0\u4ea4\uff0c\u53ef\u57fa\u4e8e\u4ee5\u4e0a\u53cd\u9988\u4fee\u6539\u540e\u91cd\u65b0\u63d0\u4ea4"}
</RadixThemesText>
<RadixThemesLink asChild={true} css={({ ["fontSize"] : "0.75rem", ["color"] : "#3b82f6", ["&:hover"] : ({ ["textDecoration"] : "underline" }) })}>

<NextLink href={"/assignments"} passHref={true}>

{"\u524d\u5f80\u91cd\u65b0\u63d0\u4ea4 \u2192"}
</NextLink>
</RadixThemesLink>
</RadixThemesBox>
</RadixThemesBox>
</RadixThemesBox>
</RadixThemesBox>
</RadixThemesFlex>
</RadixThemesBox>
</RadixThemesFlex>
<NextHead>

<title>

{"OA-EPP \u00b7 \u6210\u7ee9\u4e0e\u53cd\u9988"}
</title>
<meta content={"favicon.ico"} property={"og:image"}/>
</NextHead>
</ErrorBoundary>
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

export default function Component() {
    




  return (
    <Errorboundary_59401012a381ea4ac4dd9131cc4a29b6/>
  )
}
