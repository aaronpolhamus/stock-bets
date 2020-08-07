import React from 'react'
import styled from 'styled-components'
import { simplifyCurrency } from 'components/functions/formattingHelpers'
import { breakpoints } from 'design-tokens'

const SimplifiedCurrency = ({ value }) => (
  <span title={value.toLocaleString()}>{simplifyCurrency(value)}</span>
)

const AuxiliarText = styled.span`
  color: ${(props) => props.color || 'var(--color-text-gray)'};
  font-weight: bold;
  font-size: var(--font-size-min);
  line-height: 1.2;
`

const SmallText = styled.span`
  color: ${(props) => props.color || 'inherit'};
  font-size: var(--font-size-min);
`

const SectionTitle = styled.h2`
  color: ${(props) => props.color || 'var(--color-text-primary)'};
  font-size: var(--font-size-normal);
  font-weight: bold;
  margin-bottom: var(--space-200);
`

const TitlePage = styled.h1`
  font-size: var(--font-size-xlarge)
`

const TextButton = styled.button`
  background-color: transparent;
  border: none;
  color: ${(props) => props.color || 'var(--text-primary)'};
  font-size: ${(props) => props.size || 'var(--font-size-min)'};
  padding: 0;
`

const FlexRow = styled.div`
  align-items: ${(props) => props.align || 'center'};
  display: flex;
  justify-content: ${(props) => props.justify || 'center'};
  width: 100%;
`

const AlignText = styled.div`
  width: 100%;
  text-align: ${(props) => props.align || 'left'};
  button {
    display: inline-block;
  }
`

const FormFooter = styled.div`
  margin-top: var(--space-400);
  text-align: ${(props) => props.align || 'right'};
`

const Label = styled.p`
  color: var(--color-text-gray);
  font-size: var(--font-size-min);
  letter-spacing: var(--letter-spacing-smallcaps);
  margin: 0 0 var(--space-50) 0;
  text-transform: uppercase;
`

const Subtext = styled.small`
  color: var(--color-text-gray);
  display: block;
`

const SmallCaps = styled.small`
  color: ${(props) => props.color || 'var(--color-text-primary)'};
  font-size: var(--font-size-min);
  font-weight: 400;
  letter-spacing: var(--letter-spacing-smallcaps);
  text-transform: uppercase;
  @media screen and (max-width: ${props => breakpoints[props.$hideOnBreakpoint]}){
    display: none;
  }
`

const TitleCard = styled.h3`
  
`

const TextDivider = styled.span`
  font-weight: bold;
  color: var(--color-primary-darken);
`

const Flex = styled.div`
  display: flex;
  & > * + *{
    margin-left: var(--space-300);
  }
`

export {
  AlignText,
  AuxiliarText,
  Flex,
  FlexRow,
  FormFooter,
  Label,
  SectionTitle,
  SimplifiedCurrency,
  SmallCaps,
  SmallText,
  Subtext,
  TextButton,
  TextDivider,
  TitleCard,
  TitlePage
}
