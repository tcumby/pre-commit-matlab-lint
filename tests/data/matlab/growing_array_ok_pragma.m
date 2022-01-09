function anArray = growing_array()

anArray = [];
for idx=1:100
    anArray = [anArray; idx]; %#ok<AGROW>
end

end
